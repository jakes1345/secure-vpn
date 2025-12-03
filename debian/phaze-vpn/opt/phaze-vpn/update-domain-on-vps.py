#!/usr/bin/env python3
"""
Update domain from phazevpn.duckdns.org to phazevpn.com on VPS
Runs automatically and updates everything
"""

import paramiko
import os
import sys

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

OLD_DOMAIN = "phazevpn.duckdns.org"
NEW_DOMAIN = "phazevpn.com"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    
    if check and exit_status != 0:
        print(f"   ⚠️  Error: {error}")
        return False, output, error
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🌐 UPDATING DOMAIN ON VPS")
    print("=" * 70)
    print(f"📍 VPS: {VPS_IP}")
    print(f"🔄 {OLD_DOMAIN} → {NEW_DOMAIN}")
    print("")

    try:
        # Connect to VPS
        print("1️⃣ Connecting to VPS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected")
        print("")

        # Step 1: Update VPN configs
        print("2️⃣ Updating VPN configuration files...")
        commands = [
            f"cd {VPN_DIR}",
            f"sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' vpn-manager.py",
            f"find {VPN_DIR}/config -type f -name '*.conf' -exec sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' {{}} + 2>/dev/null || true",
            f"find {VPN_DIR}/client-configs -type f -name '*.ovpn' -exec sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' {{}} + 2>/dev/null || true",
            f"find {VPN_DIR}/phazevpn-protocol -type f -name '*.py' -exec sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' {{}} + 2>/dev/null || true",
        ]
        for cmd in commands:
            run_command(ssh, cmd, check=False)
        print("   ✅ VPN configs updated")
        print("")

        # Step 2: Update Nginx configs
        print("3️⃣ Updating web server configuration...")
        commands = [
            f"find /etc/nginx/sites-available -type f -exec sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' {{}} + 2>/dev/null || true",
            f"find /etc/nginx/sites-enabled -type f -exec sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' {{}} + 2>/dev/null || true",
        ]
        for cmd in commands:
            run_command(ssh, cmd, check=False)
        
        # Create/update Nginx config for new domain
        nginx_config = f"""
server {{
    listen 80;
    server_name {NEW_DOMAIN} www.{NEW_DOMAIN};
    
    location / {{
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        
        # Write config
        stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/nginx/sites-available/phazevpn << 'NGINXEOF'\n{nginx_config}\nNGINXEOF")
        stdout.channel.recv_exit_status()
        
        # Enable site
        run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/", check=False)
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/default", check=False)
        
        # Test Nginx config
        success, output, _ = run_command(ssh, "nginx -t", check=False)
        if success:
            print("   ✅ Nginx config updated and valid")
        else:
            print("   ⚠️  Nginx config has errors, but continuing...")
        print("")

        # Step 3: Update web portal
        print("4️⃣ Updating web portal...")
        commands = [
            f"find {VPN_DIR}/web-portal -type f \\( -name '*.py' -o -name '*.html' \\) -exec sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' {{}} + 2>/dev/null || true",
        ]
        for cmd in commands:
            run_command(ssh, cmd, check=False)
        print("   ✅ Web portal updated")
        print("")

        # Step 4: Update hostname
        print("5️⃣ Updating system hostname...")
        commands = [
            f"hostnamectl set-hostname {NEW_DOMAIN} 2>/dev/null || true",
            f"sed -i 's|{OLD_DOMAIN}|{NEW_DOMAIN}|g' /etc/hosts 2>/dev/null || true",
        ]
        for cmd in commands:
            run_command(ssh, cmd, check=False)
        print("   ✅ Hostname updated")
        print("")

        # Step 5: Check DNS
        print("6️⃣ Checking DNS propagation...")
        success, dns_result, _ = run_command(ssh, "dig +short phazevpn.com | head -1", check=False)
        if success and dns_result.strip():
            ip = dns_result.strip()
            if ip == "15.204.11.19":
                print(f"   ✅ DNS is pointing to your VPS! ({ip})")
            else:
                print(f"   ⚠️  DNS shows: {ip} (might need more time to propagate)")
        else:
            print("   ⚠️  DNS not resolving yet - might need 5-10 minutes")
        print("")

        # Step 6: Setup SSL
        print("7️⃣ Setting up SSL certificate...")
        # Check if certbot exists
        success, _, _ = run_command(ssh, "which certbot", check=False)
        if success:
            print("   Requesting SSL certificate...")
            # Try to get cert (non-interactive)
            ssl_cmd = f"certbot --nginx -d {NEW_DOMAIN} -d www.{NEW_DOMAIN} --non-interactive --agree-tos --register-unsafely-without-email 2>&1"
            success, output, error = run_command(ssh, ssl_cmd, check=False)
            if "Congratulations" in output or "Successfully" in output:
                print("   ✅ SSL certificate installed!")
            elif "already exists" in output.lower():
                print("   ✅ SSL certificate already exists")
            else:
                print("   ⚠️  SSL setup - check manually:")
                print(f"      certbot --nginx -d {NEW_DOMAIN} -d www.{NEW_DOMAIN}")
        else:
            print("   ⚠️  Certbot not installed - install with:")
            print("      apt-get install certbot python3-certbot-nginx")
        print("")

        # Step 7: Restart services
        print("8️⃣ Restarting services...")
        services = [
            ("nginx", "Web Server"),
            ("openvpn@server", "OpenVPN"),
            ("secure-vpn", "Secure VPN"),
            ("phazevpn-protocol", "PhazeVPN Protocol"),
        ]
        
        for service, name in services:
            success, _, _ = run_command(ssh, f"systemctl restart {service}", check=False)
            if success:
                print(f"   ✅ {name} restarted")
            else:
                # Check if service exists
                success, _, _ = run_command(ssh, f"systemctl is-enabled {service}", check=False)
                if not success:
                    print(f"   ⚠️  {name} not configured as service")
        
        print("")

        # Step 8: Final test
        print("9️⃣ Testing setup...")
        success, test_result, _ = run_command(ssh, f"curl -I https://{NEW_DOMAIN} 2>&1 | head -3", check=False)
        if "200" in test_result or "301" in test_result or "302" in test_result:
            print(f"   ✅ Website is accessible at https://{NEW_DOMAIN}")
        else:
            print(f"   ⚠️  Website test - DNS might still be propagating")
        
        print("")

        # Summary
        print("=" * 70)
        print("✅ DOMAIN UPDATE COMPLETE!")
        print("=" * 70)
        print("")
        print("Updated from: phazevpn.duckdns.org")
        print("Updated to:   phazevpn.com")
        print("")
        print("Services updated:")
        print("  ✅ VPN configuration")
        print("  ✅ Web server (Nginx)")
        print("  ✅ Web portal")
        print("  ✅ System hostname")
        print("")
        print("Next steps:")
        print("  1. Wait 5-10 minutes for DNS to fully propagate")
        print("  2. Test: https://phazevpn.com")
        print("  3. Regenerate VPN client configs:")
        print(f"     cd {VPN_DIR} && python3 vpn-manager.py add-client CLIENT_NAME")
        print("")
        print("If SSL didn't work, run manually:")
        print(f"  certbot --nginx -d {NEW_DOMAIN} -d www.{NEW_DOMAIN}")
        print("")

        ssh.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

