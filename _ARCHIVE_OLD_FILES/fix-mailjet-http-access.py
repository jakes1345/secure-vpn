#!/usr/bin/env python3
"""
Fix Mailjet validation - serve file via HTTP (before HTTPS redirect)
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔧 FIXING MAILJET VALIDATION - HTTP ACCESS")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Read current config
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/default")
    config = stdout.read().decode()
    
    print("Current config structure:")
    if 'listen 80' in config:
        print("✅ HTTP server block exists")
    if 'listen 443' in config:
        print("✅ HTTPS server block exists")
    print("")
    
    # Check if validation location exists in HTTP block
    if 'location = /91b8b604' in config:
        print("✅ Validation location exists")
    else:
        print("⚠️  Adding validation location to HTTP block...")
        
        # Add location block to HTTP server (before redirect)
        validation_block = """    # Mailjet validation file - must be before redirect
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain always;
        add_header Content-Length 0 always;
    }

"""
        
        # Insert in HTTP server block (before the return 301 redirect)
        if 'server {' in config and 'listen 80' in config:
            # Find HTTP server block and insert before redirect
            lines = config.split('\n')
            new_lines = []
            in_http_block = False
            block_added = False
            
            for line in lines:
                if 'listen 80' in line:
                    in_http_block = True
                
                # Insert before return 301 in HTTP block
                if in_http_block and 'return 301' in line and not block_added:
                    new_lines.append(validation_block)
                    block_added = True
                
                new_lines.append(line)
                
                if in_http_block and line.strip() == '}' and block_added:
                    in_http_block = False
            
            config = '\n'.join(new_lines)
            
            # Also add to HTTPS block
            if 'listen 443' in config and 'location / {' in config:
                https_validation = """    # Mailjet validation file
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain always;
        add_header Content-Length 0 always;
    }

"""
                config = config.replace('    location / {', https_validation + '    location / {')
            
            # Write updated config
            sftp = ssh.open_sftp()
            with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
                f.write(config)
            sftp.close()
            
            print("✅ Added validation location blocks")
    
    # Test and reload
    print("")
    print("Testing nginx config...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    test_result = stdout.read().decode()
    print(test_result)
    
    if "syntax is ok" in test_result:
        print("✅ Config valid")
        print("Reloading nginx...")
        ssh.exec_command("systemctl reload nginx")
        print("✅ Nginx reloaded")
    else:
        print("❌ Config error!")
        print(stderr.read().decode())
    
    # Test both HTTP and HTTPS
    print("")
    print("Testing file access:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost/91b8b604cb8207b4a71c14cd62205b33.txt | head -3")
    print("HTTP:", stdout.read().decode().strip())
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -I https://localhost/91b8b604cb8207b4a71c14cd62205b33.txt 2>/dev/null | head -3")
    print("HTTPS:", stdout.read().decode().strip())
    
    print("")
    print("=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print("")
    print("File should now be accessible via:")
    print("  http://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("  https://phazevpn.duckdns.org/91b8b604cb8207b4a71c14cd62205b33.txt")
    print("")
    print("Try validating in Mailjet again!")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

