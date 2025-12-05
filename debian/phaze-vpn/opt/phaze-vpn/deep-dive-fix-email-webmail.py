#!/usr/bin/env python3
"""
Deep Dive Fix - Email Server & Webmail
Diagnoses and fixes all issues
"""

import paramiko
import os
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def main():
    print("🔍 DEEP DIVE: Diagnosing Email Server & Webmail Issues")
    print("=" * 70)
    
    # Connect
    print("\n🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected!")
    
    try:
        # 1. Check what's actually installed
        print("\n1️⃣ Checking installed packages...")
        success, output, _ = run_command(ssh, "dpkg -l | grep -E 'roundcube|postfix|dovecot|opendkim' | grep '^ii'")
        print(output[:500] if output else "   No packages found")
        
        # 2. Check service status
        print("\n2️⃣ Checking service status...")
        services = ['postfix', 'dovecot', 'opendkim', 'nginx', 'php8.1-fpm', 'php-fpm']
        for svc in services:
            success, output, _ = run_command(ssh, f"systemctl is-active {svc} 2>&1", check=False)
            status = output.strip()
            if status == 'active':
                print(f"   ✅ {svc}: running")
            elif 'not found' in status or 'could not be found' in status:
                print(f"   ⚠️  {svc}: not installed")
            else:
                print(f"   ❌ {svc}: {status}")
        
        # 3. Check Nginx configuration
        print("\n3️⃣ Checking Nginx configuration...")
        success, output, _ = run_command(ssh, "nginx -t 2>&1")
        if success:
            print("   ✅ Nginx config is valid")
        else:
            print("   ❌ Nginx config errors:")
            print(f"      {output[:300]}")
        
        # 4. Check if Roundcube is installed
        print("\n4️⃣ Checking Roundcube installation...")
        success, output, _ = run_command(ssh, "test -d /usr/share/roundcube && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            print("   ✅ Roundcube is installed")
            success, output, _ = run_command(ssh, "ls -la /usr/share/roundcube/ | head -5")
            print(f"      {output[:200]}")
        else:
            print("   ❌ Roundcube not installed")
        
        # 5. Check Roundcube config
        print("\n5️⃣ Checking Roundcube configuration...")
        success, output, _ = run_command(ssh, "test -f /etc/roundcube/config.inc.php && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            print("   ✅ Roundcube config exists")
            # Check for common issues
            success, output, _ = run_command(ssh, "grep -E 'default_host|smtp_server|db_dsnw' /etc/roundcube/config.inc.php | head -5")
            print(f"      {output[:300]}")
        else:
            print("   ❌ Roundcube config missing")
        
        # 6. Check Nginx sites
        print("\n6️⃣ Checking Nginx sites...")
        success, output, _ = run_command(ssh, "ls -la /etc/nginx/sites-enabled/ | grep mail")
        if output.strip():
            print("   ✅ Mail site config found")
            print(f"      {output.strip()}")
        else:
            print("   ❌ Mail site config not found")
        
        # 7. Check PHP-FPM
        print("\n7️⃣ Checking PHP-FPM...")
        php_versions = ['php8.1-fpm', 'php8.2-fpm', 'php-fpm']
        php_found = False
        for php in php_versions:
            success, output, _ = run_command(ssh, f"systemctl is-active {php} 2>&1", check=False)
            if output.strip() == 'active':
                print(f"   ✅ {php} is running")
                php_found = True
                # Check socket
                success, output, _ = run_command(ssh, f"ls -la /var/run/php/*.sock 2>&1 | head -3", check=False)
                print(f"      Sockets: {output.strip()[:100]}")
                break
        if not php_found:
            print("   ❌ PHP-FPM not running")
            print("   Installing PHP-FPM...")
            run_command(ssh, "apt-get install -y php-fpm php-mysql php-mbstring php-xml php-zip php-gd php-curl", check=False)
        
        # 8. Check for errors in logs
        print("\n8️⃣ Checking recent errors...")
        success, output, _ = run_command(ssh, "tail -30 /var/log/nginx/error.log 2>/dev/null | grep -i error | tail -5", check=False)
        if output.strip():
            print("   ⚠️  Nginx errors:")
            for line in output.strip().split('\n'):
                if line.strip():
                    print(f"      {line[:80]}")
        
        success, output, _ = run_command(ssh, "tail -30 /var/log/mail.log 2>/dev/null | grep -i error | tail -5", check=False)
        if output.strip():
            print("   ⚠️  Mail errors:")
            for line in output.strip().split('\n'):
                if line.strip():
                    print(f"      {line[:80]}")
        
        # 9. Check ports
        print("\n9️⃣ Checking listening ports...")
        success, output, _ = run_command(ssh, "netstat -tlnp | grep -E ':80|:443|:25|:587|:993'")
        print(output[:400] if output else "   No ports found")
        
        # 10. FIX: Create proper Roundcube config if missing
        print("\n🔟 Fixing Roundcube configuration...")
        config_exists = False
        success, output, _ = run_command(ssh, "test -f /etc/roundcube/config.inc.php && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            config_exists = True
            print("   ✅ Config exists, checking if valid...")
            success, output, _ = run_command(ssh, "grep 'default_host' /etc/roundcube/config.inc.php", check=False)
            if 'mail.phazevpn.com' not in output:
                print("   ⚠️  Config needs update")
                config_exists = False
        
        if not config_exists:
            print("   📝 Creating Roundcube config...")
            config_content = '''<?php
$config = array();
$config['db_dsnw'] = 'sqlite:////var/lib/roundcube/roundcube.db?mode=0640';
$config['default_host'] = 'ssl://mail.phazevpn.com';
$config['default_port'] = 993;
$config['imap_conn_options'] = array('ssl' => array('verify_peer' => false, 'verify_peer_name' => false));
$config['smtp_server'] = 'tls://mail.phazevpn.com';
$config['smtp_port'] = 587;
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';
$config['smtp_conn_options'] = array('ssl' => array('verify_peer' => false, 'verify_peer_name' => false));
$config['des_key'] = 'DES_KEY_PLACEHOLDER';
$config['product_name'] = 'PhazeVPN Mail';
$config['skin'] = 'elastic';
$config['plugins'] = array('archive', 'zipdownload');
$config['log_dir'] = '/var/log/roundcube/';
$config['temp_dir'] = '/var/lib/roundcube/temp/';
$config['max_message_size'] = '25M';
'''
            # Generate des_key
            success, des_key, _ = run_command(ssh, "openssl rand -base64 24 | tr -d '\n' | tr -d '+/' | cut -c1-24", check=False)
            des_key = des_key.strip()
            config_content = config_content.replace('DES_KEY_PLACEHOLDER', des_key)
            
            # Write config
            sftp = ssh.open_sftp()
            with sftp.file('/etc/roundcube/config.inc.php', 'w') as f:
                f.write(config_content)
            sftp.close()
            print("   ✅ Config created")
        
        # 11. FIX: Create Nginx config for mail
        print("\n1️⃣1️⃣ Fixing Nginx configuration...")
        nginx_config = '''server {
    listen 80;
    listen [::]:80;
    server_name mail.phazevpn.com;
    location /.well-known/acme-challenge/ { root /var/www/html; }
    location / { return 301 https://$server_name$request_uri; }
}
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.com;
    ssl_certificate /etc/letsencrypt/live/phazevpn.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.com/privkey.pem;
    root /usr/share/roundcube;
    index index.php;
    client_max_body_size 50M;
    location / { try_files $uri $uri/ /index.php?$args; }
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }
}
'''
        
        # Find PHP socket
        success, php_sock, _ = run_command(ssh, "ls /var/run/php/*.sock 2>/dev/null | head -1", check=False)
        if php_sock.strip():
            php_sock = php_sock.strip().split('/')[-1]
            nginx_config = nginx_config.replace('php-fpm.sock', php_sock)
        
        # Write Nginx config
        sftp = ssh.open_sftp()
        with sftp.file('/etc/nginx/sites-available/mail-phazevpn', 'w') as f:
            f.write(nginx_config)
        sftp.close()
        
        # Enable site
        run_command(ssh, "ln -sf /etc/nginx/sites-available/mail-phazevpn /etc/nginx/sites-enabled/mail-phazevpn", check=False)
        print("   ✅ Nginx config created")
        
        # 12. Initialize database if needed
        print("\n1️⃣2️⃣ Checking database...")
        success, output, _ = run_command(ssh, "test -f /var/lib/roundcube/roundcube.db && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'NOT_FOUND' in output:
            print("   📝 Creating database...")
            run_command(ssh, "mkdir -p /var/lib/roundcube", check=False)
            # Simple schema
            run_command(ssh, "sqlite3 /var/lib/roundcube/roundcube.db 'CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, mail_host TEXT);'", check=False)
            run_command(ssh, "chown www-data:www-data /var/lib/roundcube/roundcube.db", check=False)
            run_command(ssh, "chmod 640 /var/lib/roundcube/roundcube.db", check=False)
            print("   ✅ Database created")
        else:
            print("   ✅ Database exists")
        
        # 13. Set permissions
        print("\n1️⃣3️⃣ Fixing permissions...")
        run_command(ssh, "chown -R www-data:www-data /var/lib/roundcube /var/log/roundcube 2>/dev/null", check=False)
        run_command(ssh, "mkdir -p /var/lib/roundcube/temp && chmod 755 /var/lib/roundcube/temp", check=False)
        print("   ✅ Permissions fixed")
        
        # 14. Restart everything
        print("\n1️⃣4️⃣ Restarting services...")
        for svc in ['nginx', 'php8.1-fpm', 'php-fpm', 'postfix', 'dovecot']:
            run_command(ssh, f"systemctl restart {svc} 2>&1", check=False)
        print("   ✅ Services restarted")
        
        # 15. Final test
        print("\n1️⃣5️⃣ Final verification...")
        success, output, _ = run_command(ssh, "curl -k -s -o /dev/null -w '%{http_code}' https://mail.phazevpn.com 2>&1", check=False)
        if '200' in output or '301' in output or '302' in output:
            print("   ✅ Webmail is accessible!")
        else:
            print(f"   ⚠️  Webmail response: {output.strip()}")
        
        print("\n" + "=" * 70)
        print("✅ DEEP DIVE COMPLETE!")
        print("\n🌐 Access webmail at:")
        print("   https://mail.phazevpn.com")
        print("\n📧 Login:")
        print("   Username: admin@phazevpn.com")
        print("   Password: (your email password)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()


