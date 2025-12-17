#!/usr/bin/env python3
"""
Setup HTTPS with Let's Encrypt for phazevpn.com
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔒 SETTING UP HTTPS")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # ============================================================
    # 1. INSTALL CERTBOT
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  INSTALLING CERTBOT")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('which certbot && echo "INSTALLED" || echo "NOT_INSTALLED"')
    certbot_status = stdout.read().decode().strip()
    
    if 'INSTALLED' not in certbot_status:
        print("   Installing certbot...")
        stdin, stdout, stderr = ssh.exec_command('''
        apt-get update -qq
        apt-get install -y certbot python3-certbot-nginx 2>&1 | tail -5
        ''')
        install_output = stdout.read().decode()
        print(install_output)
    else:
        print("   ✅ Certbot already installed")
    
    # ============================================================
    # 2. GET SSL CERTIFICATE
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  GETTING SSL CERTIFICATE")
    print("="*80)
    
    # Check if cert already exists
    stdin, stdout, stderr = ssh.exec_command('test -f /etc/letsencrypt/live/phazevpn.com/fullchain.pem && echo "EXISTS" || echo "NOT_EXISTS"')
    cert_exists = stdout.read().decode().strip()
    
    if 'EXISTS' in cert_exists:
        print("   ✅ SSL certificate already exists")
    else:
        print("   Getting SSL certificate from Let's Encrypt...")
        print("   ⚠️  This will require:")
        print("      - Domain phazevpn.com pointing to this VPS")
        print("      - Port 80 open for verification")
        print("      - Email for certificate expiration notices")
        
        # Run certbot (non-interactive)
        stdin, stdout, stderr = ssh.exec_command('''
        certbot certonly --nginx -d phazevpn.com --non-interactive --agree-tos --email admin@phazevpn.com --redirect 2>&1
        ''')
        certbot_output = stdout.read().decode()
        certbot_error = stderr.read().decode()
        
        print("   Certbot output:")
        print(certbot_output[:500])
        if certbot_error:
            print(f"   Errors: {certbot_error[:300]}")
        
        if 'Congratulations' in certbot_output or 'Successfully' in certbot_output:
            print("   ✅ Certificate obtained!")
        else:
            print("   ⚠️  Certificate may not have been obtained")
            print("   You may need to run manually:")
            print("   certbot --nginx -d phazevpn.com")
    
    # ============================================================
    # 3. CONFIGURE NGINX FOR HTTPS
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  CONFIGURING NGINX FOR HTTPS")
    print("="*80)
    
    # Read current Nginx config
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/etc/nginx/sites-enabled/phazevpn', 'r') as f:
            nginx_config = f.read().decode('utf-8')
    except:
        # Try default location
        try:
            with sftp.open('/etc/nginx/sites-available/phazevpn', 'r') as f:
                nginx_config = f.read().decode('utf-8')
        except:
            print("   ⚠️  Could not read Nginx config, creating new one...")
            nginx_config = ""
    
    # Create HTTPS config
    if 'listen 443' not in nginx_config:
        print("   Creating HTTPS Nginx configuration...")
        
        https_config = '''
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.com www.phazevpn.com;
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main site
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name phazevpn.com www.phazevpn.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/phazevpn.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.com/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/phazevpn_access.log;
    error_log /var/log/nginx/phazevpn_error.log;
    
    # Proxy to Flask app
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
'''
        
        # Write config
        with sftp.open('/etc/nginx/sites-available/phazevpn', 'w') as f:
            f.write(https_config.encode('utf-8'))
        
        # Enable site
        stdin, stdout, stderr = ssh.exec_command('''
        ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn
        nginx -t 2>&1
        ''')
        nginx_test = stdout.read().decode()
        print(f"   Nginx test: {nginx_test[:200]}")
        
        if 'syntax is ok' in nginx_test.lower():
            print("   ✅ Nginx config is valid")
            
            # Reload Nginx
            stdin, stdout, stderr = ssh.exec_command('systemctl reload nginx')
            print("   ✅ Nginx reloaded")
        else:
            print("   ❌ Nginx config has errors")
    else:
        print("   ✅ Nginx already configured for HTTPS")
    
    sftp.close()
    
    # ============================================================
    # 4. UPDATE FLASK APP FOR HTTPS
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  UPDATING FLASK APP FOR HTTPS")
    print("="*80)
    
    # Read app.py
    sftp = ssh.open_sftp()
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
        app_content = f.read().decode('utf-8')
    
    # Update HTTPS detection
    if 'HTTPS_ENABLED' not in app_content or 'request.is_secure' not in app_content:
        print("   Updating app.py to detect HTTPS...")
        
        # Add HTTPS detection
        https_detection = '''
# Detect HTTPS from X-Forwarded-Proto header (set by Nginx)
def is_https():
    """Detect if request is HTTPS"""
    return request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'

# Update cookie settings based on HTTPS
if is_https() if hasattr(request, 'is_secure') else False:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_NAME'] = '__Secure-VPN-Session'
else:
    # Check environment variable as fallback
    is_https_env = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'
    app.config['SESSION_COOKIE_SECURE'] = is_https_env
    app.config['SESSION_COOKIE_NAME'] = '__Secure-VPN-Session' if is_https_env else 'VPN-Session'
'''
        
        # Insert after cookie config
        if '# Update cookie settings based on HTTPS' not in app_content:
            # Find where to insert
            insert_point = app_content.find("app.config['SESSION_REFRESH_EACH_REQUEST']")
            if insert_point > 0:
                # Find end of that line
                line_end = app_content.find('\n', insert_point)
                # Insert after the cookie config block
                app_content = app_content[:line_end] + '\n' + https_detection + app_content[line_end:]
                
                with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
                    f.write(app_content.encode('utf-8'))
                print("   ✅ Updated app.py")
            else:
                print("   ⚠️  Could not find insertion point")
        else:
            print("   ✅ HTTPS detection already in app.py")
    else:
        print("   ✅ App.py already configured for HTTPS")
    
    sftp.close()
    
    # Set environment variable
    print("\n   Setting HTTPS_ENABLED environment variable...")
    stdin, stdout, stderr = ssh.exec_command('''
    # Add to systemd service
    if ! grep -q "HTTPS_ENABLED=true" /etc/systemd/system/phazevpn-portal.service; then
        sed -i '/\[Service\]/a Environment="HTTPS_ENABLED=true"' /etc/systemd/system/phazevpn-portal.service
        systemctl daemon-reload
        systemctl restart phazevpn-portal
        echo "✅ Updated service file"
    else
        echo "✅ Already configured"
    fi
    ''')
    env_output = stdout.read().decode()
    print(env_output)
    
    # ============================================================
    # 5. SETUP AUTO-RENEWAL
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  SETTING UP AUTO-RENEWAL")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('''
    # Test renewal
    certbot renew --dry-run 2>&1 | tail -5
    ''')
    renewal_test = stdout.read().decode()
    print(f"   Renewal test: {renewal_test[:200]}")
    
    # Check if cron job exists
    stdin, stdout, stderr = ssh.exec_command('crontab -l 2>&1 | grep certbot || echo "NO_CRON"')
    cron_check = stdout.read().decode()
    if 'NO_CRON' in cron_check:
        print("   Adding auto-renewal cron job...")
        stdin, stdout, stderr = ssh.exec_command('''
        (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --nginx") | crontab -
        echo "✅ Cron job added"
        ''')
        cron_output = stdout.read().decode()
        print(cron_output)
    else:
        print("   ✅ Auto-renewal already configured")
    
    # ============================================================
    # 6. TEST HTTPS
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  TESTING HTTPS")
    print("="*80)
    
    time.sleep(2)
    
    # Test HTTPS endpoint
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -o /dev/null -w "HTTP %{http_code}" https://phazevpn.com/login 2>&1 || echo "HTTPS_FAILED"
    ''')
    https_test = stdout.read().decode().strip()
    print(f"   HTTPS test: {https_test}")
    
    if '200' in https_test:
        print("   ✅ HTTPS is working!")
    elif 'HTTPS_FAILED' in https_test:
        print("   ⚠️  HTTPS test failed - may need DNS propagation")
    else:
        print(f"   ⚠️  HTTPS returned: {https_test}")
    
    # Test HTTP redirect
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}" http://phazevpn.com/login 2>&1
    ''')
    redirect_test = stdout.read().decode().strip()
    print(f"   HTTP redirect: {redirect_test}")
    
    if '301' in redirect_test or '302' in redirect_test:
        print("   ✅ HTTP redirects to HTTPS!")
    
    print("\n" + "="*80)
    print("✅ HTTPS SETUP COMPLETE")
    print("="*80)
    print("\n🌐 Your site should now be available at:")
    print("   https://phazevpn.com")
    print("\n⚠️  If HTTPS doesn't work immediately:")
    print("   1. Make sure DNS is pointing to this VPS")
    print("   2. Wait a few minutes for DNS propagation")
    print("   3. Check firewall allows port 443")
    print("   4. Run manually: certbot --nginx -d phazevpn.com")
    
    ssh.close()

if __name__ == "__main__":
    main()

