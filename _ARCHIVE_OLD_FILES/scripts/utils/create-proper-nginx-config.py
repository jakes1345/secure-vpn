#!/usr/bin/env python3
"""
Create proper nginx config with Mailjet validation
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

nginx_config = """server {
    listen 80;
    server_name phazevpn.duckdns.org 15.204.11.19;
    
    # Mailjet validation file - MUST be before redirect
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain always;
        add_header Content-Length 0 always;
    }
    
    # Redirect everything else to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name phazevpn.duckdns.org 15.204.11.19;

    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Mailjet validation file
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain always;
        add_header Content-Length 0 always;
    }

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
"""

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("=" * 60)
    print("🔧 CREATING PROPER NGINX CONFIG")
    print("=" * 60)
    print("")
    
    # Backup current config
    print("1️⃣ Backing up current config...")
    ssh.exec_command("cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup")
    print("   ✅ Backed up")
    print("")
    
    # Write new config
    print("2️⃣ Writing new nginx config...")
    sftp = ssh.open_sftp()
    with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
        f.write(nginx_config)
    sftp.close()
    print("   ✅ Config written")
    print("")
    
    # Test config
    print("3️⃣ Testing nginx config...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    test_result = stdout.read().decode()
    print(test_result)
    
    if "syntax is ok" in test_result:
        print("   ✅ Config is valid")
        print("")
        print("4️⃣ Reloading nginx...")
        ssh.exec_command("systemctl reload nginx")
        print("   ✅ Nginx reloaded")
    else:
        print("   ❌ Config error!")
        print("   Restoring backup...")
        ssh.exec_command("cp /etc/nginx/sites-enabled/default.backup /etc/nginx/sites-enabled/default")
        print("   ✅ Backup restored")
        ssh.close()
        exit(1)
    
    # Test both HTTP and HTTPS
    print("")
    print("5️⃣ Testing file access...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost/91b8b604cb8207b4a71c14cd62205b33.txt 2>&1 | head -3")
    http_result = stdout.read().decode()
    print("HTTP:", http_result.strip())
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -I https://localhost/91b8b604cb8207b4a71c14cd62205b33.txt 2>&1 | head -3")
    https_result = stdout.read().decode()
    print("HTTPS:", https_result.strip())
    
    print("")
    print("=" * 60)
    print("✅ NGINX CONFIG UPDATED")
    print("=" * 60)
    print("")
    print("Validation file should now work via:")
    print("  http://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("  https://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("")
    print("Try validating in Mailjet now!")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

