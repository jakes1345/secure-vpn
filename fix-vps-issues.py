#!/usr/bin/env python3
"""
Fix all identified VPS issues
"""
import paramiko
import os
from pathlib import Path
import time

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')

def connect_vps():
    """Connect to VPS using SSH key or password"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    
    raise Exception("Failed to connect to VPS")

def run_cmd(ssh, cmd, desc):
    """Run command and return output"""
    print(f"  ⚙️  {desc}...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status == 0:
        print(f"  ✅ Success")
        return True, output
    else:
        print(f"  ⚠️  Warning: {error[:100] if error else 'Command failed'}")
        return False, error

def fix():
    """Fix all issues"""
    print("=" * 80)
    print("🔧 FIXING VPS ISSUES")
    print("=" * 80)
    print()
    
    ssh = connect_vps()
    print(f"✅ Connected to {VPS_HOST}\n")
    
    try:
        # 1. Wait for apt lock to clear
        print("📋 Step 1: Checking for apt lock...")
        run_cmd(ssh, 
            "timeout 30 bash -c 'while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 1; done' && echo 'unlocked' || echo 'still locked'",
            "Wait for apt lock"
        )
        time.sleep(2)
        print()
        
        # 2. Setup Dead Man's Switch service
        print("📋 Step 2: Setting up Dead Man's Switch...")
        
        # Check if setup script exists
        stdin, stdout, stderr = ssh.exec_command("test -f /opt/phaze-vpn/setup-dead-mans-switch.sh && echo 'exists' || echo 'missing'")
        if 'exists' in stdout.read().decode():
            # Run setup script (skip apt update if locked)
            run_cmd(ssh,
                "bash /opt/phaze-vpn/setup-dead-mans-switch.sh 2>&1 | grep -v 'dpkg.*lock' || true",
                "Run Dead Man's Switch setup"
            )
        else:
            print("  ⚠️  Setup script not found, creating service manually...")
            # Create service file manually
            service_content = """[Unit]
Description=PhazeVPN Dead Man's Switch
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phaze-vpn
ExecStart=/usr/bin/python3 /opt/phaze-vpn/dead-mans-switch.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
            sftp = ssh.open_sftp()
            with sftp.file('/etc/systemd/system/phazevpn-deadswitch.service', 'w') as f:
                f.write(service_content)
            sftp.close()
            
            run_cmd(ssh,
                "systemctl daemon-reload && systemctl enable phazevpn-deadswitch.service && systemctl start phazevpn-deadswitch.service",
                "Enable and start Dead Man's Switch"
            )
        print()
        
        # 3. Check and fix Shadowsocks service
        print("📋 Step 3: Checking Shadowsocks service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active shadowsocks-phazevpn.service 2>&1")
        if 'active' not in stdout.read().decode().lower():
            # Check if process is running
            stdin, stdout, stderr = ssh.exec_command("pgrep -f 'ss-server' && echo 'running' || echo 'not running'")
            if 'running' in stdout.read().decode():
                print("  ℹ️  Shadowsocks is running but not as a service (may be started manually)")
            else:
                print("  ⚠️  Shadowsocks not running - checking service file...")
                stdin, stdout, stderr = ssh.exec_command("test -f /etc/systemd/system/shadowsocks-phazevpn.service && echo 'exists' || echo 'missing'")
                if 'missing' in stdout.read().decode():
                    print("  ⚠️  Shadowsocks service file missing - service may not be configured")
                else:
                    run_cmd(ssh,
                        "systemctl start shadowsocks-phazevpn.service && systemctl enable shadowsocks-phazevpn.service",
                        "Start Shadowsocks service"
                    )
        else:
            print("  ✅ Shadowsocks service is active")
        print()
        
        # 4. Check and fix Web Portal service
        print("📋 Step 4: Checking Web Portal service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web-portal.service 2>&1")
        if 'active' not in stdout.read().decode().lower():
            # Check if process is running
            stdin, stdout, stderr = ssh.exec_command("pgrep -f 'app.py' && echo 'running' || echo 'not running'")
            if 'running' in stdout.read().decode():
                print("  ℹ️  Web Portal is running but not as a service (may be started manually)")
            else:
                print("  ⚠️  Web Portal not running - checking service file...")
                stdin, stdout, stderr = ssh.exec_command("test -f /etc/systemd/system/phazevpn-web-portal.service && echo 'exists' || echo 'missing'")
                if 'missing' in stdout.read().decode():
                    print("  ⚠️  Web Portal service file missing - creating it...")
                    # Create web portal service
                    service_content = """[Unit]
Description=PhazeVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phaze-vpn/web-portal
Environment="FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-default-secret-key-change-me}"
Environment="VPN_SERVER_IP=phazevpn.com"
Environment="VPN_SERVER_HOST=phazevpn.com"
ExecStart=/usr/bin/python3 /opt/phaze-vpn/web-portal/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
                    sftp = ssh.open_sftp()
                    with sftp.file('/etc/systemd/system/phazevpn-web-portal.service', 'w') as f:
                        f.write(service_content)
                    sftp.close()
                    
                    run_cmd(ssh,
                        "systemctl daemon-reload && systemctl enable phazevpn-web-portal.service && systemctl start phazevpn-web-portal.service",
                        "Enable and start Web Portal service"
                    )
                else:
                    run_cmd(ssh,
                        "systemctl start phazevpn-web-portal.service && systemctl enable phazevpn-web-portal.service",
                        "Start Web Portal service"
                    )
        else:
            print("  ✅ Web Portal service is active")
        print()
        
        # 5. Set environment variables (create .env file)
        print("📋 Step 5: Setting environment variables...")
        env_content = """# PhazeVPN Environment Variables
FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-$(openssl rand -hex 32)}
VPN_SERVER_IP=phazevpn.com
VPN_SERVER_HOST=phazevpn.com
"""
        
        # Generate a secure secret key
        stdin, stdout, stderr = ssh.exec_command("openssl rand -hex 32")
        secret_key = stdout.read().decode().strip()
        
        env_content_final = f"""# PhazeVPN Environment Variables
FLASK_SECRET_KEY={secret_key}
VPN_SERVER_IP=phazevpn.com
VPN_SERVER_HOST=phazevpn.com
"""
        
        sftp = ssh.open_sftp()
        try:
            with sftp.file('/opt/phaze-vpn/web-portal/.env', 'w') as f:
                f.write(env_content_final)
            print("  ✅ Created .env file with environment variables")
        except Exception as e:
            print(f"  ⚠️  Could not create .env file: {e}")
        sftp.close()
        print()
        
        # 6. Verify everything
        print("📋 Step 6: Verifying fixes...")
        print()
        
        services_to_check = [
            'phazevpn-go.service',
            'shadowsocks-phazevpn.service',
            'phazevpn-web-portal.service',
            'phazevpn-deadswitch.service',
        ]
        
        for service in services_to_check:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
            status = stdout.read().decode().strip()
            if 'active' in status.lower():
                print(f"  ✅ {service}: {status}")
            else:
                print(f"  ⚠️  {service}: {status}")
        
        print()
        
        # 7. Summary
        print("=" * 80)
        print("✅ FIXES APPLIED")
        print("=" * 80)
        print()
        print("📝 Next Steps:")
        print("  1. Check service status: systemctl status phazevpn-deadswitch.service")
        print("  2. View logs: journalctl -u phazevpn-deadswitch.service -f")
        print("  3. Restart web portal to load new env vars: systemctl restart phazevpn-web-portal.service")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("✅ Connection closed")

if __name__ == '__main__':
    fix()

