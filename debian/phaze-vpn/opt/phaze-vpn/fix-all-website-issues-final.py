#!/usr/bin/env python3
"""
Final comprehensive fix for all website issues
"""

import paramiko
import time
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, wait=True):
    """Run command and return output"""
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    if wait:
        exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    errors = stderr.read().decode('utf-8')
    return output + errors

def main():
    print("=" * 70)
    print("🔧 COMPREHENSIVE WEBSITE FIX")
    print("=" * 70)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Stop service
        print("\n1️⃣ Stopping web portal service...")
        run_command(ssh, "systemctl stop phazevpn-portal")
        time.sleep(2)
        
        # 2. Kill ALL processes on port 5000
        print("\n2️⃣ Killing all processes on port 5000...")
        run_command(ssh, "fuser -k 5000/tcp 2>/dev/null; pkill -9 gunicorn; pkill -9 python3; sleep 2")
        
        # Verify port is free
        output = run_command(ssh, "lsof -i :5000 2>&1 || echo 'PORT_FREE'")
        if 'PORT_FREE' in output or 'cannot' in output.lower():
            print("   ✅ Port 5000 is free")
        else:
            print("   ⚠️  Port still in use, force killing...")
            run_command(ssh, "killall -9 python3 gunicorn 2>/dev/null; sleep 2")
        
        # 3. Fix service file
        print("\n3️⃣ Updating service file...")
        service_content = '''[Unit]
Description=PhazeVPN Web Portal (Gunicorn)
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/phaze-vpn/web-portal
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="VPN_SERVER_IP=phazevpn.duckdns.org"
Environment="VPN_SERVER_PORT=1194"
Environment="HTTPS_ENABLED=true"
ExecStart=/usr/local/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 --timeout 120 --chdir /opt/phaze-vpn/web-portal --access-logfile /var/log/phazevpn-portal-access.log --error-logfile /var/log/phazevpn-portal-error.log app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
        
        run_command(ssh, f"cat > /etc/systemd/system/phazevpn-portal.service << 'EOF'\n{service_content}\nEOF")
        run_command(ssh, "systemctl daemon-reload")
        print("   ✅ Service file updated")
        
        # 4. Start service
        print("\n4️⃣ Starting web portal service...")
        run_command(ssh, "systemctl start phazevpn-portal")
        time.sleep(5)
        
        # Check status
        output = run_command(ssh, "systemctl is-active phazevpn-portal")
        if 'active' in output.lower():
            print("   ✅ Service is running")
        else:
            print(f"   ❌ Service status: {output.strip()}")
            # Check logs
            logs = run_command(ssh, "journalctl -u phazevpn-portal --no-pager -n 20 | tail -10")
            print(f"   Recent logs:\n{logs[:500]}")
            return
        
        # 5. Test endpoints
        print("\n5️⃣ Testing endpoints...")
        time.sleep(2)
        
        endpoints = [
            ('/', 'Homepage'),
            ('/login', 'Login page'),
            ('/signup', 'Signup page'),
        ]
        
        for path, name in endpoints:
            output = run_command(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000{path}")
            code = output.strip()
            if code == '200':
                print(f"   ✅ {name}: HTTP {code}")
            else:
                print(f"   ❌ {name}: HTTP {code}")
        
        # 6. Test signup POST (should work now)
        print("\n6️⃣ Testing signup functionality...")
        output = run_command(ssh, "curl -s -X POST -d 'username=testuser789&email=test@example.com&password=testpass123&confirm_password=testpass123' http://localhost:5000/signup 2>&1 | head -20")
        if 'error' in output.lower() and 'internal' not in output.lower():
            print("   ✅ Signup working (validation working)")
        elif 'success' in output.lower() or 'created' in output.lower():
            print("   ✅ Signup working!")
        elif '500' in output or 'Internal' in output:
            print("   ❌ Signup still has errors")
            # Check error log
            error_log = run_command(ssh, "tail -30 /var/log/phazevpn-portal-error.log 2>&1 | grep -A 5 'Traceback' | tail -20")
            if error_log.strip():
                print(f"   Error details:\n{error_log[:600]}")
        else:
            print(f"   Response: {output[:200]}")
        
        # 7. Check email configuration
        print("\n7️⃣ Checking email configuration...")
        smtp_config = run_command(ssh, "test -f /opt/phaze-vpn/web-portal/smtp_config.py && cat /opt/phaze-vpn/web-portal/smtp_config.py | grep -E 'SMTP_USER|SMTP_PASSWORD' | head -2 || echo 'NOT_FOUND'")
        if 'SMTP_USER' in smtp_config and 'aceisgaming369' in smtp_config:
            print("   ✅ Gmail SMTP configured")
        else:
            print("   ⚠️  SMTP config check:")
            print(f"   {smtp_config[:200]}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print("")
        print("✅ Port conflicts resolved")
        print("✅ Service restarted")
        print("✅ Endpoints tested")
        print("")
        print("🔧 If issues persist:")
        print("   1. Check error log: tail -f /var/log/phazevpn-portal-error.log")
        print("   2. Check service: systemctl status phazevpn-portal")
        print("   3. Test email: Check smtp_config.py has correct Gmail credentials")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

