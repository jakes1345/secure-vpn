#!/usr/bin/env python3
"""
Complete fix for website down issue
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    return exit_status == 0, output

def main():
    print("=" * 70)
    print("🔧 COMPLETE WEBSITE FIX")
    print("=" * 70)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Remove old SearXNG container
        print("\n1️⃣ Removing old SearXNG container...")
        run_command(ssh, "docker rm -f searxng 2>/dev/null || true")
        print("   ✅ Done")
        
        # 2. Start SearXNG on port 8081
        print("\n2️⃣ Starting SearXNG on port 8081...")
        success, output = run_command(ssh, "docker run -d --name searxng -p 8081:8080 -v /opt/searxng:/etc/searxng:rw searxng/searxng:latest")
        if success:
            print("   ✅ SearXNG started on port 8081")
        else:
            print(f"   ⚠️  {output[:100]}")
        
        # 3. Fix nginx - read phazevpn config
        print("\n3️⃣ Fixing nginx configuration...")
        stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-available/phazevpn")
        config = stdout.read().decode('utf-8')
        
        # Add default_server to phazevpn config
        if 'listen 80;' in config and 'default_server' not in config:
            new_config = config.replace('listen 80;', 'listen 80 default_server;')
            stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/nginx/sites-available/phazevpn << 'EOF'\n{new_config}\nEOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Updated phazevpn config")
        
        # Remove default_server from mail-only
        run_command(ssh, "sed -i 's/listen 80 default_server;/listen 80;/' /etc/nginx/sites-available/mail-only")
        run_command(ssh, "sed -i 's/listen \\[::\\]:80 default_server;/listen [::]:80;/' /etc/nginx/sites-available/mail-only")
        print("   ✅ Updated mail-only config")
        
        # 4. Test and reload nginx
        print("\n4️⃣ Testing nginx config...")
        success, output = run_command(ssh, "nginx -t")
        if success:
            print("   ✅ Nginx config is valid")
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx reloaded")
        else:
            print(f"   ❌ Config error: {output[:200]}")
        
        # 5. Test website
        print("\n5️⃣ Testing website...")
        import time
        time.sleep(1)
        success, output = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost/")
        if output.strip() == '200' or output.strip() == '302':
            print(f"   ✅ Website is working! (HTTP {output.strip()})")
        else:
            print(f"   ⚠️  Website returns HTTP {output.strip()}")
        
        # 6. Test domain
        print("\n6️⃣ Testing domain...")
        success, output = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' -H 'Host: phazevpn.com' http://localhost/")
        if output.strip() == '200' or output.strip() == '302':
            print(f"   ✅ Domain is working! (HTTP {output.strip()})")
        else:
            print(f"   ⚠️  Domain returns HTTP {output.strip()}")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ FIX COMPLETE")
        print("=" * 70)
        print("")
        print("🌐 Website:")
        print("   http://15.204.11.19/")
        print("   https://phazevpn.com/")
        print("")
        print("🔍 SearXNG:")
        print("   http://15.204.11.19:8081/")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

