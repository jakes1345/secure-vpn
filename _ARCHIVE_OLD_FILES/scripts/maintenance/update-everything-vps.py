#!/usr/bin/env python3
"""
Comprehensive update script - Verifies and updates everything on VPS
"""

import paramiko
import os
from pathlib import Path
import time

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')
VPS_DIR = "/opt/phaze-vpn"
PROTOCOL_DIR = f"{VPS_DIR}/phazevpn-protocol-go"

def connect_vps():
    """Connect to VPS"""
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
        print(f"  ⚠️  Warning: {error[:100]}")
        return False, error

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS"""
    sftp = ssh.open_sftp()
    try:
        # Create directory if needed
        remote_dir = os.path.dirname(remote_path)
        ssh.exec_command(f"mkdir -p {remote_dir}")
        
        sftp.put(local_path, remote_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False

def main():
    print("=" * 70)
    print("🔄 Comprehensive VPS Update & Verification")
    print("=" * 70)
    print()
    
    ssh = connect_vps()
    print("✅ Connected to VPS\n")
    
    try:
        # Step 1: Stop old Python server
        print("📋 Step 1: Stopping old Python server...")
        run_cmd(ssh,
            "systemctl stop phazevpn-protocol.service 2>/dev/null; "
            "systemctl disable phazevpn-protocol.service 2>/dev/null; "
            "pkill -9 -f phazevpn-server-production 2>/dev/null; "
            "echo 'stopped'",
            "Stop old Python server"
        )
        time.sleep(2)
        print()
        
        # Step 2: Upload latest Go server files
        print("📋 Step 2: Uploading latest Go server files...")
        # Use current directory (where script is run from)
        script_dir = Path(__file__).parent.absolute()
        local_go_dir = script_dir / "phazevpn-protocol-go"
        
        # Upload key files (including new performance optimizations and abuse prevention)
        files_to_upload = [
            ("main.go", "main.go"),
            ("go.mod", "go.mod"),
            ("internal/server/server.go", "internal/server/server.go"),
            ("internal/server/handlers.go", "internal/server/handlers.go"),
            ("internal/server/keyexchange.go", "internal/server/keyexchange.go"),
            ("internal/server/performance.go", "internal/server/performance.go"),
            ("internal/server/mempool.go", "internal/server/mempool.go"),
            ("internal/security/abuse_prevention.go", "internal/security/abuse_prevention.go"),  # NEW: Abuse prevention
            ("internal/crypto/manager.go", "internal/crypto/manager.go"),
            ("internal/tun/manager.go", "internal/tun/manager.go"),
            ("internal/protocol/packet.go", "internal/protocol/packet.go"),
            ("internal/obfuscation/shadowsocks.go", "internal/obfuscation/shadowsocks.go"),
            ("internal/obfuscation/v2ray.go", "internal/obfuscation/v2ray.go"),
            ("internal/obfuscation/manager.go", "internal/obfuscation/manager.go"),
            ("internal/wireguard/manager.go", "internal/wireguard/manager.go"),
            ("internal/client/config.go", "internal/client/config.go"),
            ("scripts/optimize-kernel.sh", "scripts/optimize-kernel.sh"),
            ("scripts/create-client.sh", "scripts/create-client.sh"),
        ]
        
        uploaded = 0
        for local_file, remote_file in files_to_upload:
            local_path = local_go_dir / local_file
            remote_path = f"{PROTOCOL_DIR}/{remote_file}"
            
            if local_path.exists():
                if upload_file(ssh, str(local_path), remote_path):
                    uploaded += 1
                    print(f"  ✅ {local_file}")
                else:
                    print(f"  ⚠️  Failed: {local_file}")
            else:
                print(f"  ⚠️  Not found: {local_file}")
        
        print(f"\n  ✅ Uploaded {uploaded}/{len(files_to_upload)} files\n")
        
        # Step 3: Rebuild Go server
        print("📋 Step 3: Rebuilding Go server...")
        run_cmd(ssh,
            f"cd {PROTOCOL_DIR} && "
            "export PATH=$PATH:/usr/local/go/bin && "
            "mkdir -p internal/security && "  # Create security directory if needed
            "/usr/local/go/bin/go mod tidy",
            "Tidy Go modules"
        )
        
        run_cmd(ssh,
            f"cd {PROTOCOL_DIR} && "
            "export PATH=$PATH:/usr/local/go/bin && "
            "/usr/local/go/bin/go build -o phazevpn-server-go main.go && "
            "chmod +x phazevpn-server-go && "
            "ls -lh phazevpn-server-go",
            "Build Go server with abuse prevention"
        )
        print()
        
        # Step 4: Apply kernel optimizations
        print("📋 Step 4: Applying kernel optimizations...")
        run_cmd(ssh,
            f"bash {PROTOCOL_DIR}/scripts/optimize-kernel.sh",
            "Apply kernel optimizations"
        )
        print()
        
        # Step 5: Update systemd service (use port 51821 for now)
        print("📋 Step 5: Updating systemd service...")
        service_content = f"""[Unit]
Description=PhazeVPN Protocol Server (Go)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={PROTOCOL_DIR}
Environment="PATH=/usr/local/go/bin:/usr/bin:/bin"
ExecStart={PROTOCOL_DIR}/phazevpn-server-go -host 0.0.0.0 -port 51821 -network 10.9.0.0/24
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
        
        # Write service file
        sftp = ssh.open_sftp()
        with sftp.file('/etc/systemd/system/phazevpn-go.service', 'w') as f:
            f.write(service_content)
        sftp.close()
        
        run_cmd(ssh,
            "systemctl daemon-reload && "
            "systemctl enable phazevpn-go.service && "
            "systemctl restart phazevpn-go.service",
            "Reload and restart service"
        )
        time.sleep(3)
        print()
        
        # Step 6: Verify everything
        print("📋 Step 6: Verifying everything...")
        
        # Check services
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl is-active phazevpn-go.service && echo '✅ Go Server' || echo '❌ Go Server'"
        )
        print(f"  {stdout.read().decode().strip()}")
        
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl is-active shadowsocks-phazevpn.service && echo '✅ Shadowsocks' || echo '❌ Shadowsocks'"
        )
        print(f"  {stdout.read().decode().strip()}")
        
        # Check processes
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep -E '[p]hazevpn-server-go' | head -1"
        )
        process = stdout.read().decode().strip()
        if process:
            print(f"  ✅ Process running: {process.split()[1]}")
        else:
            print("  ❌ No process found")
        
        # Check ports
        stdin, stdout, stderr = ssh.exec_command(
            "ss -tuln | grep -E '(51821|8388)'"
        )
        ports = stdout.read().decode().strip()
        if ports:
            print(f"  ✅ Ports listening:")
            for line in ports.split('\n'):
                if line.strip():
                    print(f"     {line.strip()}")
        else:
            print("  ⚠️  No ports listening")
        
        # Check logs
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u phazevpn-go.service -n 5 --no-pager | tail -3"
        )
        logs = stdout.read().decode().strip()
        if logs:
            print(f"\n  📝 Recent logs:")
            for line in logs.split('\n'):
                if line.strip():
                    print(f"     {line.strip()[:80]}")
        
        print()
        
        # Step 7: Summary
        print("=" * 70)
        print("✅ Update Complete!")
        print("=" * 70)
        print()
        print("📊 Current Status:")
        stdin, stdout, stderr = ssh.exec_command(
            "echo 'Services:' && "
            "systemctl is-active phazevpn-go.service shadowsocks-phazevpn.service && "
            "echo '' && "
            "echo 'Ports:' && "
            "ss -tuln | grep -E '(51821|8388)'"
        )
        print(stdout.read().decode())
        
        print("\n📝 Useful Commands:")
        print("  systemctl status phazevpn-go.service")
        print("  journalctl -u phazevpn-go.service -f")
        print("  systemctl restart phazevpn-go.service")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("✅ Connection closed")

if __name__ == "__main__":
    main()
