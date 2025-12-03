#!/usr/bin/env python3
"""
Fix securevpn config - proper location block placement
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

# Complete config with validation file BEFORE redirect
securevpn_config = """server {
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
    print("🔧 FIXING SECUREVPN CONFIG - FINAL")
    print("=" * 60)
    print("")
    
    # Backup
    print("1️⃣ Backing up...")
    ssh.exec_command("cp /etc/nginx/sites-enabled/securevpn /etc/nginx/sites-enabled/securevpn.backup")
    print("   ✅ Backed up")
    print("")
    
    # Write config
    print("2️⃣ Writing config...")
    sftp = ssh.open_sftp()
    with sftp.file('/etc/nginx/sites-enabled/securevpn', 'w') as f:
        f.write(securevpn_config)
    sftp.close()
    print("   ✅ Config written")
    print("")
    
    # Test
    print("3️⃣ Testing...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    test_result = stdout.read().decode()
    print(test_result)
    
    if "syntax is ok" in test_result:
        print("   ✅ Valid")
        print("")
        print("4️⃣ Reloading...")
        ssh.exec_command("systemctl reload nginx")
        print("   ✅ Reloaded")
    else:
        print("   ❌ Error!")
        ssh.close()
        exit(1)
    
    # Test HTTP
    print("")
    print("5️⃣ Testing HTTP...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost/91b8b604cb8207b4a71c14cd62205b33.txt 2>&1 | head -5")
    http_result = stdout.read().decode()
    print(http_result)
    
    if "200" in http_result:
        print("   ✅ HTTP 200 OK!")
    else:
        print("   ⚠️  Still redirecting")
    
    # Test body
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost/91b8b604cb8207b4a71c14cd62205b33.txt | wc -c")
    body_size = stdout.read().decode().strip()
    print(f"   Body size: {body_size} bytes (should be 0)")
    
    print("")
    print("=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print("")
    print("Test URLs:")
    print("  http://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("  https://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

