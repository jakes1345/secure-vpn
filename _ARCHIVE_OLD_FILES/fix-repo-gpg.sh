#!/bin/bash
# Fix GPG key and nginx configuration for repository

set -e

echo "=========================================="
echo "Fixing PhazeVPN Repository"
echo "=========================================="
echo ""

python3 << 'PYTHON_SCRIPT'
import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
REPO_DIR = "/var/www/phazevpn-repo"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    
    # 1. Create GPG key
    print("\n[1/4] Creating GPG key...")
    stdin, stdout, stderr = ssh.exec_command("gpg --list-keys admin@phazevpn.duckdns.org 2>&1")
    key_check = stdout.read().decode()
    
    if "admin@phazevpn.duckdns.org" not in key_check:
        print("   Generating new GPG key...")
        # Create key using expect or direct command
        keygen_cmd = """gpg --batch --gen-key << GPGEOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: PhazeVPN Team
Name-Email: admin@phazevpn.duckdns.org
Expire-Date: 0
%commit
GPGEOF"""
        
        stdin, stdout, stderr = ssh.exec_command(keygen_cmd)
        time.sleep(3)  # Wait for key generation
        stdout.channel.recv_exit_status()
        print("   ✅ GPG key generated")
    else:
        print("   ✅ GPG key already exists")
    
    # 2. Export GPG key
    print("\n[2/4] Exporting GPG key...")
    stdin, stdout, stderr = ssh.exec_command(f"gpg --armor --export admin@phazevpn.duckdns.org > {REPO_DIR}/gpg-key.asc 2>&1")
    export_output = stderr.read().decode()
    
    # Check file size
    stdin, stdout, stderr = ssh.exec_command(f"wc -c {REPO_DIR}/gpg-key.asc")
    file_size = stdout.read().decode().strip().split()[0]
    print(f"   Key file size: {file_size} bytes")
    
    if int(file_size) > 500:
        print("   ✅ GPG key exported successfully")
    else:
        print(f"   ⚠️  Key file seems too small: {export_output[:200]}")
    
    # Fix permissions
    ssh.exec_command(f"chmod 644 {REPO_DIR}/gpg-key.asc")
    ssh.exec_command(f"chown root:root {REPO_DIR}/gpg-key.asc")
    
    # 3. Update main nginx config
    print("\n[3/4] Updating nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/securevpn")
    main_config = stdout.read().decode()
    
    if "location /repo" not in main_config:
        print("   Adding repository location to main config...")
        
        # Find where to insert (before closing brace of server block)
        repo_location = """
    # PhazeVPN APT Repository
    location /repo {
        alias /var/www/phazevpn-repo;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        
        # GPG key
        location ~ gpg-key\\.asc$ {
            alias /var/www/phazevpn-repo/gpg-key.asc;
            add_header Content-Type "application/pgp-keys";
            default_type application/pgp-keys;
        }
        
        # Package files
        location ~ \\.deb$ {
            add_header Content-Type application/octet-stream;
        }
        
        # Packages index
        location ~ Packages(\\.gz|\\.bz2)?$ {
            add_header Content-Type "text/plain; charset=utf-8";
        }
    }
"""
        
        # Insert before the last closing brace
        if main_config.rstrip().endswith('}'):
            # Find the last location block or insert before final }
            lines = main_config.split('\n')
            # Find last non-empty line before final }
            insert_idx = len(lines) - 1
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == '}' and i > 0:
                    # Check if previous line is also }
                    if i > 0 and lines[i-1].strip() != '}':
                        insert_idx = i
                        break
            
            lines.insert(insert_idx, repo_location)
            new_config = '\n'.join(lines)
            
            # Write new config
            stdin, stdout, stderr = ssh.exec_command("cat > /tmp/securevpn-nginx.conf", get_pty=False)
            stdin.write(new_config)
            stdin.close()
            stdout.channel.recv_exit_status()
            
            # Move to final location
            ssh.exec_command("cp /tmp/securevpn-nginx.conf /etc/nginx/sites-available/securevpn")
            
            # Test nginx
            stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
            nginx_test = stdout.read().decode()
            if "successful" in nginx_test or "test is successful" in nginx_test:
                ssh.exec_command("systemctl reload nginx")
                print("   ✅ Nginx config updated and reloaded")
            else:
                print(f"   ⚠️  Nginx test failed: {nginx_test[:400]}")
        else:
            print("   ⚠️  Could not parse nginx config structure")
    else:
        print("   ✅ Repository location already configured")
    
    # 4. Test access
    print("\n[4/4] Testing repository access...")
    time.sleep(1)  # Wait for nginx reload
    
    stdin, stdout, stderr = ssh.exec_command("curl -sI https://phazevpn.duckdns.org/repo/gpg-key.asc 2>&1 | head -3")
    https_test = stdout.read().decode()
    print(f"   HTTPS: {https_test[:150]}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -sI http://phazevpn.duckdns.org/repo/gpg-key.asc 2>&1 | head -3")
    http_test = stdout.read().decode()
    print(f"   HTTP: {http_test[:150]}")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("✅ Repository Fix Complete!")
    print("=" * 60)
    print("\nTry adding the repository again:")
    print("  sudo bash /opt/phaze-vpn/add-phazevpn-repo.sh")
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "✅ Fix complete!"

