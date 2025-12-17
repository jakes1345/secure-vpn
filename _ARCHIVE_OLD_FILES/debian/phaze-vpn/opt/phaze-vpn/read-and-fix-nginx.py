#!/usr/bin/env python3
"""
Read and fix nginx config for Mailjet validation
"""

from paramiko import SSHClient, AutoAddPolicy
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Read config
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/default")
    config = stdout.read().decode()
    
    print("Current nginx config:")
    print("=" * 60)
    print(config)
    print("=" * 60)
    
    # Check if validation location exists
    if 'location = /91b8b604' in config:
        print("\n✅ Validation location block EXISTS")
    else:
        print("\n❌ Validation location block MISSING")
        
        # Add it to HTTPS server block
        location_block = """    # Mailjet domain validation file
    location = /91b8b604cb8207b4a71c14cd62205b33.txt {
        return 200 '';
        add_header Content-Type text/plain always;
        add_header Content-Length 0 always;
    }

"""
        
        # Insert before main location / in HTTPS block
        if 'server {' in config and 'listen 443' in config:
            # Find the HTTPS server block and insert before location /
            lines = config.split('\n')
            new_lines = []
            in_https_block = False
            location_added = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                
                if 'listen 443' in line:
                    in_https_block = True
                
                if in_https_block and 'location / {' in line and not location_added:
                    new_lines.insert(-1, location_block)
                    location_added = True
                
                if in_https_block and line.strip() == '}' and location_added:
                    in_https_block = False
            
            config = '\n'.join(new_lines)
            
            # Write updated config
            sftp = ssh.open_sftp()
            with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
                f.write(config)
            sftp.close()
            
            print("✅ Added validation location block")
            
            # Test and reload
            stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
            test = stdout.read().decode()
            if "syntax is ok" in test:
                ssh.exec_command("systemctl reload nginx")
                print("✅ Nginx reloaded")
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

