#!/usr/bin/env python3
"""
Fix Mailjet validation - serve file directly via nginx
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔧 FIXING MAILJET VALIDATION")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Step 1: Copy file to web root
    print("1️⃣ Copying validation file to web root...")
    ssh.exec_command("mkdir -p /var/www/html && cp /opt/secure-vpn/web-portal/static/91b8b604cb8207b4a71c14cd62205b33.txt /var/www/html/ && chmod 644 /var/www/html/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("   ✅ File copied")
    print("")
    
    # Step 2: Read current nginx config
    print("2️⃣ Reading nginx config...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/default")
    nginx_config = stdout.read().decode()
    print("   ✅ Config read")
    print("")
    
    # Step 3: Add location block for validation file (before the main location /)
    print("3️⃣ Updating nginx config...")
    location_block = """    # Mailjet validation file - serve directly from nginx
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        root /var/www/html;
        default_type text/plain;
        add_header Content-Type text/plain;
    }

"""
    
    if 'location = /91b8b604' not in nginx_config:
        # Insert before the main location / block
        nginx_config = nginx_config.replace('    location / {', location_block + '    location / {')
        
        # Write updated config
        sftp = ssh.open_sftp()
        with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
            f.write(nginx_config)
        sftp.close()
        print("   ✅ Config updated")
    else:
        print("   ℹ️  Location block already exists")
    print("")
    
    # Step 4: Test and reload nginx
    print("4️⃣ Testing nginx config...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t")
    test_result = stdout.read().decode()
    print(test_result)
    
    if "syntax is ok" in test_result:
        print("   ✅ Config is valid")
        print("")
        print("5️⃣ Reloading nginx...")
        ssh.exec_command("systemctl reload nginx")
        print("   ✅ Nginx reloaded")
    else:
        print("   ❌ Config has errors!")
        print(stderr.read().decode())
    print("")
    
    # Step 5: Test the file
    print("6️⃣ Testing validation file access...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost/91b8b604cb8207b4a71c14cd62205b33.txt | head -5")
    test_result = stdout.read().decode()
    print(test_result)
    
    if "200" in test_result:
        print("   ✅ File accessible via nginx")
    else:
        print("   ⚠️  File might not be accessible")
    print("")
    
    print("=" * 60)
    print("✅ SETUP COMPLETE")
    print("=" * 60)
    print("")
    print("Validation file should now be accessible at:")
    print("  https://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("")
    print("Try validating in Mailjet again!")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

