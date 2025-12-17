#!/usr/bin/env python3
"""
Fix base.html file and restart everything
"""

import paramiko
import base64
from pathlib import Path

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def upload_file_via_ssh(ssh, local_path, remote_path):
    """Upload file via SSH base64 encoding"""
    try:
        with open(local_path, 'rb') as f:
            content = f.read()
        
        encoded = base64.b64encode(content).decode('utf-8')
        
        # Write file in chunks to avoid command length limits
        command = f"cat > {remote_path} << 'BASEEOF'\n{encoded}\nBASEEOF\nbase64 -d {remote_path} > {remote_path}.new && mv {remote_path}.new {remote_path}"
        
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            return True, "Uploaded"
        else:
            error = stderr.read().decode()
            return False, error
    except Exception as e:
        return False, str(e)

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🔧 FIXING BASE.HTML AND RESTARTING EVERYTHING")
    print("=" * 80)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # Read local base.html
    local_base = Path("web-portal/templates/base.html")
    if not local_base.exists():
        print("❌ Local base.html not found!")
        ssh.close()
        return
    
    print(f"1️⃣ Reading local base.html ({local_base.stat().st_size} bytes)...")
    content = local_base.read_text()
    print(f"   ✅ Read {len(content)} characters")
    
    print()
    
    # Upload base.html
    print("2️⃣ Uploading base.html to VPS...")
    remote_path = "/opt/secure-vpn/web-portal/templates/base.html"
    
    # Use SFTP
    try:
        sftp = ssh.open_sftp()
        
        # Check if file exists
        try:
            sftp.stat(remote_path)
            print(f"   File exists on VPS, backing up...")
            run_command(ssh, f"cp {remote_path} {remote_path}.backup-$(date +%s)")
        except:
            print(f"   Creating new file...")
        
        # Write file
        with sftp.file(remote_path, 'w') as f:
            f.write(content)
        
        sftp.close()
        print(f"   ✅ base.html uploaded!")
        
        # Verify file size
        success, output, error = run_command(ssh, f"wc -c {remote_path}")
        if success:
            print(f"   ✅ Verified: {output}")
        
    except Exception as e:
        print(f"   ⚠️  SFTP failed, trying direct write...")
        # Alternative: direct write via SSH
        encoded = base64.b64encode(content.encode()).decode('utf-8')
        write_cmd = f"echo '{encoded}' | base64 -d > {remote_path}"
        success, output, error = run_command(ssh, write_cmd)
        if success:
            print(f"   ✅ base.html written!")
        else:
            print(f"   ❌ Failed: {error[:200]}")
            ssh.close()
            return
    
    print()
    
    # Restart Flask
    print("3️⃣ Restarting Flask app...")
    run_command(ssh, "pkill -9 -f 'python.*app.py'; sleep 2")
    
    # Start Flask
    run_command(ssh, "cd /opt/secure-vpn/web-portal && nohup python3 -u app.py > /tmp/flask-app.log 2>&1 &")
    print("   ✅ Flask restart command executed")
    
    import time
    time.sleep(3)
    
    # Test Flask
    print("4️⃣ Testing Flask response...")
    time.sleep(2)
    success, output, error = run_command(ssh, "curl -s http://127.0.0.1:5000/ | head -30")
    if success and output and len(output) > 100:
        print(f"   ✅ Flask is responding! ({len(output)} bytes)")
        print(f"   First 150 chars: {output[:150]}")
    else:
        print(f"   ⚠️  Flask response: {output[:100] if output else 'empty'}")
    
    print()
    
    # Check Nginx
    print("5️⃣ Checking Nginx...")
    success, output, error = run_command(ssh, "systemctl status nginx --no-pager | head -5")
    if success:
        if 'active (running)' in output:
            print("   ✅ Nginx is running")
        else:
            print("   ⚠️  Nginx not running, restarting...")
            run_command(ssh, "systemctl restart nginx")
    else:
        print("   ⚠️  Could not check Nginx status")
    
    print()
    
    print("=" * 80)
    print("✅ FIX COMPLETE!")
    print("=" * 80)
    print()
    print("🌐 Website should be working now!")
    print("   Check: https://phazevpn.duckdns.org")
    
    ssh.close()

if __name__ == "__main__":
    main()

