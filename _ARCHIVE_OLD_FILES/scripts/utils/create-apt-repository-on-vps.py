#!/usr/bin/env python3
"""
Set up APT repository on VPS for PhazeVPN updates
This ensures users see updates in their Update Manager automatically
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

REPO_DIR = "/var/www/phazevpn-repo"
REPO_URL = "https://phazevpn.duckdns.org/repo"

def run_command(ssh, command, description):
    """Run command on VPS"""
    print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        output = stdout.read().decode().strip()
        if output:
            print(f"    ✅ {output[:100]}")
        return True
    else:
        error = stderr.read().decode().strip()
        print(f"    ⚠️  Error: {error[:200]}")
        return False

def main():
    print("=" * 80)
    print("🔧 SETTING UP APT REPOSITORY ON VPS")
    print("=" * 80)
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print()
    
    # 1. Install required tools
    print("1️⃣ Installing repository tools...")
    commands = [
        ("apt-get update", "Updating package list"),
        ("apt-get install -y reprepro gnupg2 nginx dpkg-dev", "Installing reprepro, gnupg, nginx"),
    ]
    
    for cmd, desc in commands:
        run_command(ssh, cmd, desc)
    
    print()
    
    # 2. Create repository directory
    print("2️⃣ Creating repository structure...")
    repo_commands = [
        (f"mkdir -p {REPO_DIR}/{{conf,dists/stable/main/binary-amd64,pool/main,incoming}}", "Creating directory structure"),
        (f"chmod -R 755 {REPO_DIR}", "Setting permissions"),
    ]
    
    for cmd, desc in repo_commands:
        run_command(ssh, cmd, desc)
    
    print()
    
    # 3. Create reprepro configuration
    print("3️⃣ Configuring reprepro...")
    
    distributions_conf = """# Repository configuration for PhazeVPN
Codename: stable
Suite: stable
Architectures: amd64 i386
Components: main
Description: PhazeVPN Official Repository
SignWith: default
"""
    
    # Write distributions file
    stdin, stdout, stderr = ssh.exec_command(f"cat > {REPO_DIR}/conf/distributions << 'EOF'\n{distributions_conf}\nEOF")
    stdout.channel.recv_exit_status()
    print("    ✅ Created distributions config")
    
    options_conf = """# Reprepro options
outdir +b/.
basedir .
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > {REPO_DIR}/conf/options << 'EOF'\n{options_conf}\nEOF")
    stdout.channel.recv_exit_status()
    print("    ✅ Created options config")
    
    print()
    
    # 4. Generate GPG key (if not exists)
    print("4️⃣ Setting up GPG key...")
    key_check = run_command(ssh, f"gpg --list-secret-keys --keyid-format LONG | grep -q 'phazevpn' || echo 'no-key'", "Checking for existing key")
    
    if key_check:
        stdin, stdout, stderr = ssh.exec_command("gpg --list-secret-keys --keyid-format LONG 2>/dev/null | head -1")
        existing_key = stdout.read().decode().strip()
        
        if 'no-key' in existing_key or not existing_key:
            # Generate new key non-interactively
            print("    📝 Generating GPG key...")
            key_gen = f"""gpg --batch --gen-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Real: PhazeVPN Repository
Name-Email: admin@phazevpn.duckdns.org
Expire-Date: 0
EOF"""
            run_command(ssh, key_gen, "Generating GPG key")
    
    # Export public key
    run_command(ssh, f"gpg --armor --export admin@phazevpn.duckdns.org > {REPO_DIR}/gpg-key.asc 2>/dev/null", "Exporting public key")
    
    print()
    
    # 5. Configure Nginx to serve repository
    print("5️⃣ Configuring Nginx...")
    
    nginx_conf = f"""server {{
    listen 80;
    server_name phazevpn.duckdns.org;
    
    root {REPO_DIR};
    index index.html;
    
    location /repo {{
        alias {REPO_DIR};
        autoindex on;
        autoindex_exact_size off;
    }}
    
    location / {{
        try_files $uri $uri/ =404;
    }}
}}
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/nginx/sites-available/phazevpn-repo << 'EOF'\n{nginx_conf}\nEOF")
    stdout.channel.recv_exit_status()
    
    run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-repo /etc/nginx/sites-enabled/phazevpn-repo", "Enabling site")
    run_command(ssh, "nginx -t", "Testing Nginx config")
    run_command(ssh, "systemctl restart nginx", "Restarting Nginx")
    
    print()
    
    # 6. Create update script
    print("6️⃣ Creating package update script...")
    
    update_script = f"""#!/bin/bash
# Add new package to repository

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 /path/to/package.deb"
    exit 1
fi

DEB_FILE="$1"
REPO_DIR="{REPO_DIR}"

if [ ! -f "$DEB_FILE" ]; then
    echo "❌ Error: Package file not found: $DEB_FILE"
    exit 1
fi

echo "📦 Adding package to repository..."
cd "$REPO_DIR"
reprepro -b . includedeb stable "$DEB_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Package added successfully!"
    echo "   Repository URL: {REPO_URL}"
else
    echo "❌ Failed to add package"
    exit 1
fi
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > /usr/local/bin/phazevpn-add-package << 'EOF'\n{update_script}\nEOF")
    stdout.channel.recv_exit_status()
    run_command(ssh, "chmod +x /usr/local/bin/phazevpn-add-package", "Making script executable")
    
    print()
    print("=" * 80)
    print("✅ APT REPOSITORY SETUP COMPLETE!")
    print("=" * 80)
    print()
    print("📦 Repository Location: {REPO_DIR}")
    print("🌐 Repository URL: {REPO_URL}")
    print()
    print("📋 To add packages:")
    print("   phazevpn-add-package /path/to/phazevpn-client_2.0.0_amd64.deb")
    print()
    print("✅ Users can now add repository and get automatic updates!")
    
    ssh.close()

if __name__ == "__main__":
    main()

