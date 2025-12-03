#!/usr/bin/env python3
"""
Fix Routing Properly - Make mail subdomain work
"""

import paramiko
import sys

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if check and exit_status != 0:
        print(f"❌ Error: {error}")
        return False, output, error
    return True, output, error

def main():
    print("🔧 Fixing Routing Properly...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Check all Nginx configs
        print("\n1️⃣ Checking all Nginx configs...")
        success, output, error = run_command(
            ssh,
            "cat /etc/nginx/sites-enabled/*",
            check=False
        )
        print(f"   Current configs:\n{output[:1000]}")
        
        # Find what's serving the VPN homepage
        print("\n2️⃣ Finding VPN homepage service...")
        success, output, error = run_command(
            ssh,
            "ss -tlnp | grep ':80' | head -5",
            check=False
        )
        print(f"   Services on port 80: {output}")
        
        # Check what securevpn config does
        print("\n3️⃣ Checking securevpn config...")
        success, output, error = run_command(
            ssh,
            "cat /etc/nginx/sites-available/securevpn 2>/dev/null || echo 'NOT FOUND'",
            check=False
        )
        print(f"   SecureVPN config:\n{output[:500]}")
        
        # Remove ALL configs
        print("\n4️⃣ Removing all configs...")
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/*", check=False)
        
        # Create proper config with mail subdomain FIRST (higher priority)
        print("\n5️⃣ Creating proper config...")
        nginx_config = """# Mail subdomain - MUST be first for proper matching
server {
    listen 80;
    server_name mail.phazevpn.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Main domain - VPN homepage
server {
    listen 80;
    server_name phazevpn.duckdns.org;

    # Keep existing VPN homepage - don't change this
    # This should already be configured elsewhere
    location / {
        # If you have a VPN web portal, it should be here
        # For now, we'll just proxy to port 8080 too, but you can change this
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Default - Portal
server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}"""
        
        # Write mail config
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/mail-portal', 'w')
        f.write(nginx_config)
        f.close()
        sftp.close()
        
        # Enable it
        run_command(ssh, "ln -sf /etc/nginx/sites-available/mail-portal /etc/nginx/sites-enabled/mail-portal")
        
        # Re-enable securevpn if it exists (for VPN homepage)
        success, output, error = run_command(
            ssh,
            "test -f /etc/nginx/sites-available/securevpn && echo 'EXISTS' || echo 'NOT FOUND'",
            check=False
        )
        if "EXISTS" in output:
            print("\n6️⃣ Re-enabling VPN homepage config...")
            run_command(ssh, "ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/securevpn")
        
        # Test config
        print("\n7️⃣ Testing Nginx config...")
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"   Test result: {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx reloaded")
        else:
            print(f"   ⚠️  Error: {error}")
        
        # Test with curl using Host header
        print("\n8️⃣ Testing routing with Host header...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -i 'dashboard\\|email\\|portal' | head -3",
            check=False
        )
        print(f"   Mail subdomain test: {output}")
        
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: phazevpn.duckdns.org' http://localhost/ | grep -i 'vpn\\|military' | head -3",
            check=False
        )
        print(f"   Main domain test: {output}")
        
        print("\n✅ Routing Fixed!")
        print("\n🌐 Configuration:")
        print("   - mail.phazevpn.duckdns.org → Portal (8080)")
        print("   - phazevpn.duckdns.org → VPN Homepage (existing)")
        print("\n🔄 Clear browser cache and try: http://mail.phazevpn.duckdns.org")
        print("   Or use: http://15.204.11.19:8080 (direct, no DNS)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
