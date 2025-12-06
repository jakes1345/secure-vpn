#!/usr/bin/env python3
"""
Setup APT Repository on VPS
This allows Linux users to get updates via apt update/upgrade
"""

import paramiko
import subprocess
import os
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"\n🔧 {description}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        if output.strip():
            print(f"   ✅ {output.strip()}")
        return True, output
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error}")
        return False, output

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS"""
    sftp = ssh.open_sftp()
    try:
        sftp.put(local_path, remote_path)
        print(f"   ✅ Uploaded: {remote_path}")
        return True
    except Exception as e:
        print(f"   ❌ Error uploading {remote_path}: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("="*80)
    print("📦 SETTING UP APT REPOSITORY ON VPS")
    print("="*80)
    
    # Connect to VPS
    print("\n📡 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # ============================================================
    # 1. INSTALL REPOSITORY TOOLS
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  INSTALLING REPOSITORY TOOLS")
    print("="*80)
    
    run_command(ssh, "apt-get update", "Updating package list")
    run_command(ssh, "apt-get install -y apt-utils dpkg-dev gnupg2", 
                "Installing repository tools")
    
    # ============================================================
    # 2. CREATE REPOSITORY DIRECTORY
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CREATING REPOSITORY STRUCTURE")
    print("="*80)
    
    repo_dir = "/var/www/phazevpn-repo"
    run_command(ssh, f"mkdir -p {repo_dir}/dists/stable/main/binary-amd64", 
                "Creating repository directories")
    run_command(ssh, f"mkdir -p {repo_dir}/pool/main", 
                "Creating pool directory")
    
    # ============================================================
    # 3. GENERATE GPG KEY (if not exists)
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  SETTING UP GPG KEY")
    print("="*80)
    
    # Check if GPG key exists
    stdin, stdout, stderr = ssh.exec_command(
        "gpg --list-secret-keys --keyid-format LONG | grep -q 'phazevpn' && echo 'EXISTS' || echo 'NOT FOUND'"
    )
    has_key = "EXISTS" in stdout.read().decode()
    
    if not has_key:
        print("\n🔑 Generating GPG key for repository signing...")
        # Create key non-interactively
        gpg_batch = f"""
%no-protection
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: PhazeVPN Repository
Name-Email: admin@phazevpn.com
Expire-Date: 0
%commit
"""
        stdin, stdout, stderr = ssh.exec_command(
            f"gpg --batch --gen-key <<EOF\n{gpg_batch}\nEOF"
        )
        output = stdout.read().decode()
        if "gpg: key" in output:
            print("   ✅ GPG key generated")
        else:
            print("   ⚠️  GPG key generation (may already exist)")
    else:
        print("   ✅ GPG key already exists")
    
    # Export public key
    run_command(ssh, "gpg --armor --export phazevpn > /var/www/phazevpn-repo/KEY.gpg 2>/dev/null || gpg --armor --export admin@phazevpn.com > /var/www/phazevpn-repo/KEY.gpg 2>/dev/null || echo 'Key export failed'",
                "Exporting public key")
    
    # ============================================================
    # 4. CREATE REPOSITORY SCRIPT
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  CREATING REPOSITORY UPDATE SCRIPT")
    print("="*80)
    
    update_repo_script = f"""#!/bin/bash
# Update APT repository

REPO_DIR="{repo_dir}"
DEB_FILE="$1"

if [ ! -f "$DEB_FILE" ]; then
    echo "Usage: $0 <path-to-deb-file>"
    exit 1
fi

# Copy .deb to pool
cp "$DEB_FILE" "$REPO_DIR/pool/main/"

# Generate Packages file
cd "$REPO_DIR"
dpkg-scanpackages --arch amd64 pool/main > dists/stable/main/binary-amd64/Packages 2>/dev/null
gzip -k -f dists/stable/main/binary-amd64/Packages

# Generate Release file
cat > dists/stable/Release <<EOF
Origin: PhazeVPN
Label: PhazeVPN Repository
Suite: stable
Codename: stable
Architectures: amd64
Components: main
Description: PhazeVPN Official Repository
Date: $(date -Ru)
EOF

# Sign Release file
gpg --default-key admin@phazevpn.com --armor --detach-sign --output dists/stable/Release.gpg dists/stable/Release 2>/dev/null || \\
gpg --armor --detach-sign --output dists/stable/Release.gpg dists/stable/Release 2>/dev/null || \\
echo "Warning: Could not sign Release file"

echo "Repository updated!"
"""
    
    # Upload script
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/usr/local/bin/update-phazevpn-repo', 'w') as f:
            f.write(update_repo_script)
        ssh.exec_command("chmod +x /usr/local/bin/update-phazevpn-repo")
        print("   ✅ Repository update script created")
    except Exception as e:
        print(f"   ⚠️  Error creating script: {e}")
    finally:
        sftp.close()
    
    # ============================================================
    # 5. CONFIGURE NGINX
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  CONFIGURING NGINX")
    print("="*80)
    
    nginx_config = f"""
server {{
    listen 80;
    server_name repo.phazevpn.com;
    root {repo_dir};
    
    location / {{
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }}
    
    location ~ \\.deb$ {{
        add_header Content-Type application/octet-stream;
    }}
}}
"""
    
    # Create nginx config
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/etc/nginx/sites-available/phazevpn-repo', 'w') as f:
            f.write(nginx_config)
        ssh.exec_command("ln -sf /etc/nginx/sites-available/phazevpn-repo /etc/nginx/sites-enabled/")
        ssh.exec_command("nginx -t && systemctl reload nginx")
        print("   ✅ Nginx configured")
    except Exception as e:
        print(f"   ⚠️  Error configuring nginx: {e}")
    finally:
        sftp.close()
    
    # ============================================================
    # 6. CREATE CLIENT SETUP INSTRUCTIONS
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  CREATING CLIENT SETUP SCRIPT")
    print("="*80)
    
    client_setup = """#!/bin/bash
# Add PhazeVPN repository to your system

echo "Adding PhazeVPN repository..."

# Download and add GPG key
curl -fsSL https://phazevpn.com/repo/KEY.gpg | gpg --dearmor -o /usr/share/keyrings/phazevpn-archive-keyring.gpg

# Add repository
echo "deb [signed-by=/usr/share/keyrings/phazevpn-archive-keyring.gpg] https://phazevpn.com/repo stable main" | tee /etc/apt/sources.list.d/phazevpn.list

# Update package list
apt-get update

echo "✅ PhazeVPN repository added!"
echo "You can now install/update with: apt install phaze-vpn"
"""
    
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/var/www/phazevpn-repo/setup-repo.sh', 'w') as f:
            f.write(client_setup)
        ssh.exec_command("chmod +x /var/www/phazevpn-repo/setup-repo.sh")
        print("   ✅ Client setup script created")
    except Exception as e:
        print(f"   ⚠️  Error creating setup script: {e}")
    finally:
        sftp.close()
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("✅ APT REPOSITORY SETUP COMPLETE")
    print("="*80)
    print(f"\n📦 Repository Location: {repo_dir}")
    print(f"🌐 Repository URL: https://phazevpn.com/repo")
    print(f"\n📝 To add a new package:")
    print(f"   1. Build .deb package: ./build-deb.sh")
    print(f"   2. Upload to VPS")
    print(f"   3. Run: update-phazevpn-repo /path/to/package.deb")
    print(f"\n👥 Users add repository:")
    print(f"   curl -fsSL https://phazevpn.com/repo/setup-repo.sh | bash")
    print(f"\n🔄 Users update:")
    print(f"   apt update && apt upgrade phaze-vpn")
    
    ssh.close()

if __name__ == "__main__":
    main()

