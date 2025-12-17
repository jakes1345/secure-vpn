#!/usr/bin/env python3
"""
Fix all nginx configs - add validation to securevpn config and disable default if needed
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

validation_block = """    # Mailjet validation file - MUST be before redirect
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain always;
        add_header Content-Length 0 always;
    }

"""

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("=" * 60)
    print("🔧 FIXING ALL NGINX CONFIGS")
    print("=" * 60)
    print("")
    
    # Read securevpn config
    print("1️⃣ Reading securevpn config...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/securevpn")
    securevpn_config = stdout.read().decode()
    
    if 'location = /91b8b604' in securevpn_config:
        print("   ✅ Validation already in securevpn config")
    else:
        print("   ⚠️  Adding validation to securevpn config...")
        
        # Add to HTTP block (before redirect)
        if 'listen 80' in securevpn_config and 'return 301' in securevpn_config:
            # Insert before return 301
            securevpn_config = securevpn_config.replace(
                '    return 301',
                validation_block + '    return 301'
            )
        
        # Add to HTTPS block (before location /)
        if 'listen 443' in securevpn_config and 'location / {' in securevpn_config:
            securevpn_config = securevpn_config.replace(
                '    location / {',
                validation_block + '    location / {'
            )
        
        # Write updated config
        sftp = ssh.open_sftp()
        with sftp.file('/etc/nginx/sites-enabled/securevpn', 'w') as f:
            f.write(securevpn_config)
        sftp.close()
        print("   ✅ Updated securevpn config")
    
    print("")
    print("2️⃣ Disabling default config (to avoid conflicts)...")
    ssh.exec_command("mv /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default.disabled 2>/dev/null || true")
    print("   ✅ Default config disabled")
    
    print("")
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
        print(stderr.read().decode())
        ssh.close()
        exit(1)
    
    # Test HTTP access
    print("")
    print("5️⃣ Testing HTTP access...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost/91b8b604cb8207b4a71c14cd62205b33.txt 2>&1 | head -3")
    http_result = stdout.read().decode()
    print("HTTP:", http_result.strip())
    
    if "200" in http_result:
        print("   ✅ HTTP works!")
    else:
        print("   ⚠️  HTTP still redirecting")
    
    print("")
    print("=" * 60)
    print("✅ ALL CONFIGS FIXED")
    print("=" * 60)
    print("")
    print("Try validating in Mailjet now!")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

