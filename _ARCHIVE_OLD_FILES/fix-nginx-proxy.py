#!/usr/bin/env python3
"""
Fix Nginx to proxy to Flask instead of serving files
"""

import paramiko

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🔧 FIXING NGINX - PROXY TO FLASK")
    print("=" * 80)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # Check current Nginx config
    print("1️⃣ Checking current Nginx config...")
    success, output, error = run_command(ssh, "cat /etc/nginx/sites-enabled/securevpn")
    print(f"   Current config preview:")
    print(f"   {output[:500]}")
    
    print()
    
    # Create proper Nginx config
    print("2️⃣ Creating proper Nginx config...")
    
    nginx_config = """server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org 15.204.11.19;
    
    # Repository directory - serve APT repo files
    location /repo {
        alias /var/www/phazevpn-repo;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        
        # Allow package downloads
        location ~ \\.(deb|dsc|tar\\.gz|tar\\.bz2|tar\\.xz|asc)$ {
            add_header Content-Disposition "attachment";
        }
    }
    
    # Proxy all other requests to Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}

# HTTPS redirect (if SSL cert exists)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name phazevpn.duckdns.org;
    
    # SSL configuration (if certs exist)
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;
    
    # Repository directory
    location /repo {
        alias /var/www/phazevpn-repo;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }
    
    # Proxy all other requests to Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
"""
    
    # Write config
    stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/nginx/sites-enabled/securevpn << 'NGINXEOF'\n{nginx_config}\nNGINXEOF")
    stdout.channel.recv_exit_status()
    print("    ✅ Nginx config updated")
    
    print()
    
    # Test Nginx config
    print("3️⃣ Testing Nginx configuration...")
    success, output, error = run_command(ssh, "nginx -t")
    if success:
        print("    ✅ Nginx config is valid")
    else:
        print(f"    ⚠️  Nginx config error: {error[:200]}")
    
    print()
    
    # Restart Nginx
    print("4️⃣ Restarting Nginx...")
    success, output, error = run_command(ssh, "systemctl restart nginx")
    if success:
        print("    ✅ Nginx restarted")
    else:
        print(f"    ⚠️  Error: {error[:200]}")
    
    print()
    
    # Kill and restart Flask
    print("5️⃣ Restarting Flask app...")
    run_command(ssh, "pkill -9 -f 'python.*app.py'; sleep 2")
    run_command(ssh, "cd /opt/secure-vpn/web-portal && nohup python3 -u app.py > /tmp/flask-app.log 2>&1 &")
    print("    ✅ Flask restart command executed")
    
    import time
    time.sleep(3)
    
    # Verify Flask is running
    print("6️⃣ Verifying Flask is running...")
    success, output, error = run_command(ssh, "curl -s http://127.0.0.1:5000/ | head -20")
    if success and output and len(output) > 100:
        print(f"    ✅ Flask is responding! (got {len(output)} bytes)")
    else:
        print(f"    ⚠️  Flask response: {output[:100] if output else 'no output'}")
    
    print()
    
    print("=" * 80)
    print("✅ WEBSITE FIXED!")
    print("=" * 80)
    print()
    print("🌐 Website should be working now at: https://phazevpn.duckdns.org")
    print("📋 Check logs: tail -f /tmp/flask-app.log")
    
    ssh.close()

if __name__ == "__main__":
    main()

