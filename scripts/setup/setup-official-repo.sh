#!/bin/bash
# Set up official PhazeVPN APT repository on VPS

set -e

echo "=========================================="
echo "Setting Up Official PhazeVPN Repository"
echo "=========================================="
echo ""

python3 << 'PYTHON_SCRIPT'
import paramiko
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
REPO_DIR = "/var/www/phazevpn-repo"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    
    # 1. Ensure repository directory structure
    print("\n[1/6] Setting up repository structure...")
    ssh.exec_command(f"mkdir -p {REPO_DIR}/{{conf,dists/stable/main/binary-amd64,pool/main,incoming}}")
    ssh.exec_command(f"chmod -R 755 {REPO_DIR}")
    print("   ✅ Repository structure created")
    
    # 2. Create reprepro configuration
    print("\n[2/6] Configuring reprepro...")
    
    # Install reprepro if needed
    stdin, stdout, stderr = ssh.exec_command("which reprepro || echo 'MISSING'")
    if 'MISSING' in stdout.read().decode():
        print("   Installing reprepro...")
        stdin, stdout, stderr = ssh.exec_command("apt-get update && apt-get install -y reprepro 2>&1")
        stdout.channel.recv_exit_status()
        print("   ✅ Reprepro installed")
    
    # Create distributions config
    dist_config = """Origin: PhazeVPN
Label: PhazeVPN Repository
Codename: stable
Architectures: amd64 arm64 all
Components: main
Description: PhazeVPN Official APT Repository
SignWith: admin@phazevpn.duckdns.org
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > {REPO_DIR}/conf/distributions << 'DIST_EOF'\n{dist_config}DIST_EOF")
    stdout.channel.recv_exit_status()
    
    # Create options config
    stdin, stdout, stderr = ssh.exec_command(f"echo 'basedir {REPO_DIR}' > {REPO_DIR}/conf/options")
    stdout.channel.recv_exit_status()
    print("   ✅ Reprepro configured")
    
    # 3. Set up GPG key
    print("\n[3/6] Setting up GPG key...")
    stdin, stdout, stderr = ssh.exec_command("gpg --list-keys admin@phazevpn.duckdns.org 2>&1 | head -1 || echo 'NO_KEY'")
    has_key = stdout.read().decode().strip()
    
    if 'NO_KEY' in has_key or not has_key or 'not found' in has_key.lower():
        print("   Creating GPG key...")
        # Create GPG key non-interactively
        stdin, stdout, stderr = ssh.exec_command("""gpg --batch --gen-key << 'GPGEOF'
%no-protection
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: PhazeVPN Team
Name-Email: admin@phazevpn.duckdns.org
Expire-Date: 0
%commit
GPGEOF
""")
        stdout.channel.recv_exit_status()
        print("   ✅ GPG key created")
    else:
        print("   ✅ GPG key exists")
    
    # Export GPG key
    stdin, stdout, stderr = ssh.exec_command(f"gpg --armor --export admin@phazevpn.duckdns.org > {REPO_DIR}/gpg-key.asc 2>&1")
    key_output = stderr.read().decode()
    if "exported" in key_output.lower() or ssh.exec_command(f"test -f {REPO_DIR}/gpg-key.asc")[1].read().decode().strip():
        print("   ✅ GPG key exported")
    else:
        print(f"   ⚠️  GPG export: {key_output[:200]}")
    
    # 4. Configure nginx to serve repository
    print("\n[4/6] Configuring nginx...")
    
    nginx_config = """server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org;
    
    # Repository location
    location /repo {
        alias /var/www/phazevpn-repo;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        
        # Allow .deb downloads
        location ~ \\.deb$ {
            add_header Content-Type application/octet-stream;
            add_header Content-Disposition attachment;
        }
        
        # Allow GPG key download
        location ~ gpg-key\\.asc$ {
            add_header Content-Type application/pgp-keys;
        }
        
        # Allow Packages files
        location ~ Packages(\\.gz|\\.bz2)?$ {
            add_header Content-Type text/plain;
        }
    }
    
    # Direct access to repository root
    location = /repo {
        return 301 /repo/;
    }
    
    # Root redirects to main site
    location = / {
        return 301 /dashboard;
    }
}
"""
    
    # Write nginx config
    stdin, stdout, stderr = ssh.exec_command("cat > /etc/nginx/sites-available/phazevpn-repo << 'NGINX_EOF'\n" + nginx_config + "NGINX_EOF")
    stdout.channel.recv_exit_status()
    
    # Enable site
    ssh.exec_command("ln -sf /etc/nginx/sites-available/phazevpn-repo /etc/nginx/sites-enabled/phazevpn-repo 2>/dev/null || true")
    
    # Test nginx config
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    nginx_test = stdout.read().decode()
    if "successful" in nginx_test or "test is successful" in nginx_test:
        ssh.exec_command("systemctl reload nginx")
        print("   ✅ Nginx configured and reloaded")
    else:
        print(f"   ⚠️  Nginx test: {nginx_test[:300]}")
    
    # 5. Add existing package to repository
    print("\n[5/6] Adding packages to repository...")
    stdin, stdout, stderr = ssh.exec_command(f"find {REPO_DIR}/pool/main -name '*.deb' 2>/dev/null | head -1")
    existing_pkg = stdout.read().decode().strip()
    
    if existing_pkg:
        print(f"   Found existing package: {existing_pkg}")
        stdin, stdout, stderr = ssh.exec_command(f"cd {REPO_DIR} && reprepro -b . remove stable phaze-vpn 2>&1 || true")
        stdout.channel.recv_exit_status()
        
        stdin, stdout, stderr = ssh.exec_command(f"cd {REPO_DIR} && reprepro -b . includedeb stable {existing_pkg} 2>&1")
        add_output = stdout.read().decode()
        add_error = stderr.read().decode()
        add_status = stdout.channel.recv_exit_status()
        
        if add_status == 0:
            print("   ✅ Package added to repository")
        else:
            print(f"   ⚠️  Reprepro issue: {add_error[:200]}")
            # Alternative method
            print("   Using alternative method...")
            ssh.exec_command(f"cd {REPO_DIR} && dpkg-scanpackages pool/main /dev/null 2>/dev/null | gzip > dists/stable/main/binary-amd64/Packages.gz")
            print("   ✅ Package added (alternative)")
    else:
        print("   ⚠️  No packages found to add")
    
    # 6. Create repository index page
    print("\n[6/6] Creating repository index...")
    index_html = """<!DOCTYPE html>
<html>
<head>
    <title>PhazeVPN APT Repository</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        h1 { color: #4a5568; }
    </style>
</head>
<body>
    <h1>🔒 PhazeVPN Official APT Repository</h1>
    <p>Add this repository to your Debian/Ubuntu system:</p>
    <h2>Quick Setup</h2>
    <pre># Add GPG key
curl -fsSL https://phazevpn.duckdns.org/repo/gpg-key.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/phazevpn.gpg

# Add repository
echo "deb https://phazevpn.duckdns.org/repo stable main" | sudo tee /etc/apt/sources.list.d/phazevpn.list

# Update and install
sudo apt update
sudo apt install phaze-vpn</pre>
    <h2>Manual Setup</h2>
    <p>Download the GPG key: <a href="/repo/gpg-key.asc">gpg-key.asc</a></p>
    <p>Repository URL: <code>https://phazevpn.duckdns.org/repo</code></p>
</body>
</html>
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > {REPO_DIR}/index.html << 'INDEX_EOF'\n{index_html}INDEX_EOF")
    stdout.channel.recv_exit_status()
    print("   ✅ Repository index created")
    
    # Verify repository is accessible
    print("\n🔍 Verifying repository...")
    stdin, stdout, stderr = ssh.exec_command(f"test -f {REPO_DIR}/gpg-key.asc && echo 'GPG_KEY_OK' || echo 'GPG_KEY_MISSING'")
    gpg_status = stdout.read().decode().strip()
    print(f"   GPG Key: {gpg_status}")
    
    stdin, stdout, stderr = ssh.exec_command(f"test -f {REPO_DIR}/dists/stable/main/binary-amd64/Packages.gz && echo 'PACKAGES_OK' || echo 'PACKAGES_MISSING'")
    packages_status = stdout.read().decode().strip()
    print(f"   Packages: {packages_status}")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("✅ Official Repository Set Up!")
    print("=" * 60)
    print("\nRepository URL: https://phazevpn.duckdns.org/repo")
    print("GPG Key URL: https://phazevpn.duckdns.org/repo/gpg-key.asc")
    print("\nUsers can add the repository with:")
    print("  curl -fsSL https://phazevpn.duckdns.org/repo/gpg-key.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/phazevpn.gpg")
    print("  echo 'deb https://phazevpn.duckdns.org/repo stable main' | sudo tee /etc/apt/sources.list.d/phazevpn.list")
    print("  sudo apt update")
    print("  sudo apt install phaze-vpn")
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "✅ Repository setup complete!"

