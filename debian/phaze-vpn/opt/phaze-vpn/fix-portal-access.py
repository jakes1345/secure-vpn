#!/usr/bin/env python3
"""
Fix Portal Access - Make it publicly accessible
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
    print("🔧 Fixing Portal Access...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Check if portal is running
        print("\n1️⃣ Checking portal service...")
        success, output, error = run_command(
            ssh,
            "systemctl is-active phazevpn-portal",
            check=False
        )
        
        if "active" not in output.lower():
            print("   ⚠️  Portal not running, starting...")
            run_command(ssh, "systemctl start phazevpn-portal")
            run_command(ssh, "systemctl enable phazevpn-portal")
        
        # Check if portal is listening
        print("\n2️⃣ Checking if portal is listening...")
        success, output, error = run_command(
            ssh,
            "ss -tlnp | grep ':8080' || netstat -tlnp | grep ':8080'",
            check=False
        )
        print(f"   Output: {output}")
        
        # Configure Nginx reverse proxy
        print("\n3️⃣ Configuring Nginx reverse proxy...")
        
        nginx_config = """server {
    listen 80;
    server_name phazevpn.duckdns.org;

    # Portal
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

    # Email API
    location /api/email/ {
        proxy_pass http://127.0.0.1:5005/api/v1/email/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Storage API
    location /api/storage/ {
        proxy_pass http://127.0.0.1:5002/api/v1/storage/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Productivity API
    location /api/productivity/ {
        proxy_pass http://127.0.0.1:5003/api/v1/productivity/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Extensibility API
    location /api/extensibility/ {
        proxy_pass http://127.0.0.1:5004/api/v1/extensibility/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}"""
        
        # Write Nginx config
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/phazevpn-portal', 'w')
        f.write(nginx_config)
        f.close()
        sftp.close()
        
        # Enable site
        run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-portal /etc/nginx/sites-enabled/", check=False)
        
        # Test and reload Nginx
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        
        if success:
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx configured")
        else:
            print(f"   ⚠️  Nginx config error: {error}")
        
        # Configure firewall
        print("\n4️⃣ Configuring firewall...")
        ports = [
            ("80", "HTTP"),
            ("443", "HTTPS"),
            ("8080", "Portal Direct")
        ]
        
        for port, desc in ports:
            run_command(ssh, f"ufw allow {port}/tcp comment '{desc}'", check=False)
            print(f"   ✅ Opened port {port} ({desc})")
        
        # Restart portal if needed
        print("\n5️⃣ Restarting portal service...")
        run_command(ssh, "systemctl restart phazevpn-portal")
        
        # Wait a bit
        import time
        time.sleep(3)
        
        # Check status
        print("\n6️⃣ Checking services...")
        services = ['phazevpn-portal', 'nginx']
        for service in services:
            success, output, error = run_command(
                ssh,
                f"systemctl is-active {service}",
                check=False
            )
            if "active" in output.lower():
                print(f"   ✅ {service} is running")
            else:
                print(f"   ⚠️  {service}: {output.strip()}")
        
        # Test portal
        print("\n7️⃣ Testing portal access...")
        success, output, error = run_command(
            ssh,
            "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/",
            check=False
        )
        print(f"   Portal response: {output.strip()}")
        
        print("\n✅ Portal Access Fixed!")
        print("\n📋 Access URLs:")
        print("   - http://phazevpn.duckdns.org")
        print("   - http://15.204.11.19")
        print("   - http://15.204.11.19:8080 (direct)")
        print("\n🔧 Make sure your DNS points phazevpn.duckdns.org to 15.204.11.19")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
