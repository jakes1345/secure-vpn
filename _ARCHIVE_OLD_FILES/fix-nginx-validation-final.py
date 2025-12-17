#!/usr/bin/env python3
"""
Final fix for Mailjet validation - ensure file is served correctly
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔧 FINAL FIX: MAILJET VALIDATION")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Read current config
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/default")
    config = stdout.read().decode()
    
    # Check if location block exists in HTTPS server block
    if 'location = /91b8b604' in config:
        print("✅ Location block already exists")
    else:
        print("⚠️  Location block missing - adding it...")
        
        # Find the HTTPS server block and add location before main location /
        location_block = """    # Mailjet validation file
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain;
        add_header Content-Length 0;
    }

"""
        
        # Insert before the main location / in HTTPS block
        if 'listen 443' in config and 'location / {' in config:
            config = config.replace('    location / {', location_block + '    location / {')
            
            sftp = ssh.open_sftp()
            with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
                f.write(config)
            sftp.close()
            print("✅ Added location block")
        else:
            print("❌ Could not find HTTPS server block")
    
    # Test and reload
    print("")
    print("Testing nginx config...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    test_result = stdout.read().decode()
    print(test_result)
    
    if "syntax is ok" in test_result:
        print("✅ Config valid - reloading...")
        ssh.exec_command("systemctl reload nginx")
        print("✅ Nginx reloaded")
    else:
        print("❌ Config error!")
        print(stderr.read().decode())
    
    # Final test
    print("")
    print("Final test:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I https://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt | head -5")
    print(stdout.read().decode())
    
    print("")
    print("=" * 60)
    print("✅ DONE - Try validating in Mailjet now!")
    print("=" * 60)
    print("")
    print("URL: https://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

