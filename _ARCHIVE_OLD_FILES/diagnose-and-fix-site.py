#!/usr/bin/env python3
"""
Comprehensive diagnostic and fix script for PhazeVPN site
Checks everything and fixes issues automatically
"""

from paramiko import SSHClient, AutoAddPolicy
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"
WEB_PORTAL_DIR = f"{VPN_DIR}/web-portal"

print("=" * 70)
print("🔍 COMPREHENSIVE SITE DIAGNOSTIC & FIX")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    issues_found = []
    fixes_applied = []
    
    # ============================================
    # 1. CHECK FLASK APP STATUS
    # ============================================
    print("1️⃣ Checking Flask app (app.py)...")
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'app.py' || echo 'NOT_RUNNING'")
    app_status = stdout.read().decode().strip()
    
    if app_status == "NOT_RUNNING" or not app_status:
        print("   ❌ Flask app is NOT running!")
        issues_found.append("Flask app not running")
        
        # Check if app.py exists
        stdin, stdout, stderr = ssh.exec_command(f"test -f {WEB_PORTAL_DIR}/app.py && echo 'EXISTS' || echo 'MISSING'")
        app_exists = stdout.read().decode().strip()
        
        if app_exists == "EXISTS":
            print("   🔧 Starting Flask app...")
            # Kill any stale processes
            ssh.exec_command("pkill -f app.py 2>/dev/null")
            time.sleep(1)
            
            # Start app in background
            ssh.exec_command(f"cd {WEB_PORTAL_DIR} && nohup python3 app.py > /tmp/web-portal.log 2>&1 &")
            time.sleep(3)
            
            # Verify it started
            stdin, stdout, stderr = ssh.exec_command("pgrep -f 'app.py' && echo 'RUNNING' || echo 'FAILED'")
            verify = stdout.read().decode().strip()
            
            if "RUNNING" in verify:
                print("   ✅ Flask app started!")
                fixes_applied.append("Started Flask app")
            else:
                print("   ❌ Failed to start Flask app")
                # Check logs
                stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/web-portal.log 2>&1")
                logs = stdout.read().decode()
                print(f"   Logs: {logs[:200]}")
                issues_found.append("Flask app failed to start")
        else:
            print("   ❌ app.py file not found!")
            issues_found.append("app.py file missing")
    else:
        print(f"   ✅ Flask app is running (PID: {app_status})")
    
    print("")
    
    # ============================================
    # 2. CHECK PORT 8081 LISTENING
    # ============================================
    print("2️⃣ Checking if port 8081 is listening...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep ':8081' || ss -tlnp 2>/dev/null | grep ':8081' || echo 'NOT_LISTENING'")
    port_status = stdout.read().decode().strip()
    
    if "NOT_LISTENING" in port_status or not port_status or "8081" not in port_status:
        print("   ❌ Port 8081 is NOT listening!")
        issues_found.append("Port 8081 not listening")
    else:
        print(f"   ✅ Port 8081 is listening: {port_status[:80]}")
    
    print("")
    
    # ============================================
    # 3. CHECK NGINX STATUS
    # ============================================
    print("3️⃣ Checking nginx status...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx 2>&1")
    nginx_status = stdout.read().decode().strip()
    
    if nginx_status != "active":
        print(f"   ❌ Nginx is {nginx_status}!")
        issues_found.append(f"Nginx is {nginx_status}")
        
        print("   🔧 Starting nginx...")
        ssh.exec_command("systemctl start nginx")
        time.sleep(2)
        
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx 2>&1")
        new_status = stdout.read().decode().strip()
        if new_status == "active":
            print("   ✅ Nginx started!")
            fixes_applied.append("Started nginx")
        else:
            print(f"   ❌ Failed to start nginx: {new_status}")
            issues_found.append("Nginx failed to start")
    else:
        print("   ✅ Nginx is running")
    
    print("")
    
    # ============================================
    # 4. CHECK NGINX CONFIGURATION
    # ============================================
    print("4️⃣ Checking nginx configuration...")
    
    # Check if config file exists
    stdin, stdout, stderr = ssh.exec_command("test -f /etc/nginx/sites-enabled/default && echo 'EXISTS' || test -f /etc/nginx/sites-enabled/securevpn && echo 'SECUREVPN' || echo 'MISSING'")
    config_file = stdout.read().decode().strip()
    
    if config_file == "MISSING":
        print("   ❌ No nginx config file found!")
        issues_found.append("Nginx config file missing")
    else:
        config_path = "/etc/nginx/sites-enabled/default" if config_file == "EXISTS" else "/etc/nginx/sites-enabled/securevpn"
        print(f"   📄 Config file: {config_path}")
        
        # Read config
        stdin, stdout, stderr = ssh.exec_command(f"cat {config_path}")
        nginx_config = stdout.read().decode()
        
        # Check for proxy_pass to 8081
        if "proxy_pass http://127.0.0.1:8081" in nginx_config or "proxy_pass http://localhost:8081" in nginx_config:
            print("   ✅ Nginx is configured to proxy to port 8081")
        else:
            print("   ❌ Nginx is NOT configured to proxy to port 8081!")
            issues_found.append("Nginx proxy_pass incorrect")
            
            # Check what port it's using
            if "proxy_pass" in nginx_config:
                import re
                match = re.search(r'proxy_pass\s+http://[^:]+:(\d+)', nginx_config)
                if match:
                    wrong_port = match.group(1)
                    print(f"   ⚠️  Currently proxying to port {wrong_port} instead of 8081")
            
            # Fix it
            print("   🔧 Fixing nginx configuration...")
            
            # Create proper config
            proper_config = """server {
    listen 80;
    server_name phazevpn.duckdns.org 15.204.11.19;
    
    # Mailjet validation file
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain always;
        add_header Content-Length 0 always;
    }
    
    # Redirect everything else to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
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
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
"""
            
            sftp = ssh.open_sftp()
            with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
                f.write(proper_config)
            sftp.close()
            
            print("   ✅ Config updated")
            fixes_applied.append("Fixed nginx configuration")
        
        # Test nginx config
        stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
        nginx_test = stdout.read().decode()
        
        if "syntax is ok" in nginx_test:
            print("   ✅ Nginx config syntax is valid")
        else:
            print("   ❌ Nginx config has errors!")
            print(f"   {nginx_test}")
            issues_found.append("Nginx config syntax error")
    
    print("")
    
    # ============================================
    # 5. CHECK SYSTEMD SERVICE
    # ============================================
    print("5️⃣ Checking systemd service for web portal...")
    stdin, stdout, stderr = ssh.exec_command("systemctl list-unit-files | grep -E 'phazevpn-web|secure-vpn-web|web-portal' || echo 'NOT_FOUND'")
    service_status = stdout.read().decode().strip()
    
    if "NOT_FOUND" in service_status or not service_status:
        print("   ⚠️  No systemd service found for web portal")
        print("   💡 Creating systemd service...")
        
        service_content = f"""[Unit]
Description=PhazeVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={WEB_PORTAL_DIR}
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 {WEB_PORTAL_DIR}/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        sftp = ssh.open_sftp()
        with sftp.file('/etc/systemd/system/phazevpn-web.service', 'w') as f:
            f.write(service_content)
        sftp.close()
        
        ssh.exec_command("systemctl daemon-reload")
        ssh.exec_command("systemctl enable phazevpn-web")
        ssh.exec_command("systemctl start phazevpn-web")
        time.sleep(2)
        
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
        service_active = stdout.read().decode().strip()
        
        if service_active == "active":
            print("   ✅ Systemd service created and started!")
            fixes_applied.append("Created systemd service")
        else:
            print(f"   ⚠️  Service created but status: {service_active}")
    else:
        print(f"   ✅ Service found: {service_status[:60]}")
        
        # Check if it's active
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1 || systemctl is-active secure-vpn-web 2>&1 || echo 'INACTIVE'")
        is_active = stdout.read().decode().strip()
        
        if is_active == "active":
            print("   ✅ Service is active")
        else:
            print(f"   ⚠️  Service is {is_active}, starting...")
            ssh.exec_command("systemctl start phazevpn-web || systemctl start secure-vpn-web")
            time.sleep(2)
            fixes_applied.append("Started systemd service")
    
    print("")
    
    # ============================================
    # 6. RELOAD NGINX
    # ============================================
    print("6️⃣ Reloading nginx...")
    stdin, stdout, stderr = ssh.exec_command("systemctl reload nginx 2>&1 && echo 'SUCCESS' || echo 'FAILED'")
    reload_result = stdout.read().decode().strip()
    
    if "SUCCESS" in reload_result:
        print("   ✅ Nginx reloaded")
    else:
        print(f"   ⚠️  Reload result: {reload_result}")
    
    print("")
    
    # ============================================
    # 7. TEST CONNECTIONS
    # ============================================
    print("7️⃣ Testing connections...")
    
    # Test direct Flask app
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8081/ 2>&1")
    direct_code = stdout.read().decode().strip()
    
    if direct_code == "200":
        print("   ✅ Direct connection to Flask app works (200)")
    else:
        print(f"   ⚠️  Direct connection returned: {direct_code}")
        issues_found.append(f"Flask app returned {direct_code}")
    
    # Test via nginx
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' -k https://127.0.0.1/ 2>&1")
    nginx_code = stdout.read().decode().strip()
    
    if nginx_code == "200":
        print("   ✅ Connection via nginx works (200)")
    elif nginx_code == "301" or nginx_code == "302":
        print(f"   ℹ️  Nginx returned {nginx_code} (redirect - might be normal)")
    elif nginx_code == "502":
        print("   ❌ Nginx returned 502 Bad Gateway!")
        issues_found.append("Nginx 502 Bad Gateway")
    else:
        print(f"   ⚠️  Nginx returned: {nginx_code}")
        issues_found.append(f"Nginx returned {nginx_code}")
    
    print("")
    
    # ============================================
    # 8. CHECK FIREWALL
    # ============================================
    print("8️⃣ Checking firewall...")
    stdin, stdout, stderr = ssh.exec_command("ufw status 2>&1 | head -5 || iptables -L INPUT -n | head -10")
    firewall_status = stdout.read().decode().strip()
    
    if "8081" in firewall_status or "80" in firewall_status or "443" in firewall_status:
        print("   ✅ Firewall rules found")
    else:
        print("   ⚠️  Firewall might be blocking ports")
        print("   💡 Opening ports...")
        ssh.exec_command("ufw allow 80/tcp 2>/dev/null; ufw allow 443/tcp 2>/dev/null; ufw allow 8081/tcp 2>/dev/null")
        fixes_applied.append("Opened firewall ports")
    
    print("")
    
    # ============================================
    # SUMMARY
    # ============================================
    print("=" * 70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    print("")
    
    if issues_found:
        print("❌ Issues Found:")
        for issue in issues_found:
            print(f"   - {issue}")
        print("")
    else:
        print("✅ No issues found!")
        print("")
    
    if fixes_applied:
        print("🔧 Fixes Applied:")
        for fix in fixes_applied:
            print(f"   - {fix}")
        print("")
    
    print("=" * 70)
    print("✅ DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print("")
    print("🌐 Test the site:")
    print("   https://phazevpn.duckdns.org")
    print("")
    print("📋 If issues persist, check:")
    print("   - Flask app logs: tail -f /tmp/web-portal.log")
    print("   - Nginx logs: tail -f /var/log/nginx/error.log")
    print("   - Systemd service: systemctl status phazevpn-web")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

