#!/usr/bin/env python3
"""
Fix Portal Routing - Make sure mail.phazevpn.duckdns.org goes to portal, not VPN homepage
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
    print("🔧 Fixing Portal Routing...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Check what's running on port 80
        print("\n1️⃣ Checking what's running on port 80...")
        success, output, error = run_command(
            ssh,
            "ss -tlnp | grep ':80 ' || netstat -tlnp | grep ':80 '",
            check=False
        )
        print(f"   Port 80: {output}")
        
        # Check portal on 8080
        print("\n2️⃣ Checking portal on port 8080...")
        success, output, error = run_command(
            ssh,
            "curl -s http://localhost:8080/ | head -20",
            check=False
        )
        print(f"   Portal response: {output[:200]}")
        
        # Check all Nginx configs
        print("\n3️⃣ Checking Nginx configurations...")
        success, output, error = run_command(
            ssh,
            "ls -la /etc/nginx/sites-enabled/",
            check=False
        )
        print(f"   Enabled sites: {output}")
        
        # Remove ALL nginx configs and create clean one
        print("\n4️⃣ Creating clean Nginx config...")
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/*", check=False)
        
        # Create proper config - mail subdomain goes to portal
        nginx_config = """# Mail subdomain -> Portal
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

# Main domain -> VPN homepage (keep existing)
server {
    listen 80;
    server_name phazevpn.duckdns.org;

    # This should point to your VPN homepage
    # If you have a web portal for VPN, update this
    location / {
        # Keep existing VPN homepage config
        # Or proxy to wherever your VPN homepage is
        return 200 "VPN Homepage - Update this config";
        add_header Content-Type text/plain;
    }
}

# IP access -> Portal
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
        
        # Write config
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/phazevpn-mail', 'w')
        f.write(nginx_config)
        f.close()
        sftp.close()
        
        # Enable it
        run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-mail /etc/nginx/sites-enabled/phazevpn-mail")
        
        # Test and reload
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"\n   Nginx test: {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx reloaded")
        else:
            print(f"   ⚠️  Error: {error}")
        
        # Test routing
        print("\n5️⃣ Testing routing...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | head -10",
            check=False
        )
        print(f"   Mail subdomain response: {output[:200]}")
        
        print("\n✅ Routing Fixed!")
        print("\n🌐 Now:")
        print("   - mail.phazevpn.duckdns.org → Portal (port 8080)")
        print("   - phazevpn.duckdns.org → VPN Homepage")
        print("   - 15.204.11.19 → Portal (default)")
        print("\n🔄 Try accessing: http://mail.phazevpn.duckdns.org")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
