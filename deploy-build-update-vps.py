#!/usr/bin/env python3
"""
Deploy updated code to VPS, build package there, and update repository
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
LOCAL_DIR = Path(__file__).parent

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    return None

def main():
    print("="*60)
    print("Deploy & Build Update on VPS")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected")
    print()
    
    try:
        # Step 1: Deploy updated files
        print("[1/4] Deploying updated files to VPS...")
        sftp = ssh.open_sftp()
        
        # Deploy key files
        files_to_deploy = [
            ('vpn-gui.py', f'{VPS_DIR}/vpn-gui.py'),
            ('vpn-manager.py', f'{VPS_DIR}/vpn-manager.py'),
            ('web-portal/app.py', f'{VPS_DIR}/web-portal/app.py'),
            ('debian/changelog', f'{VPS_DIR}/debian/changelog'),
            ('debian/phaze-vpn/DEBIAN/control', f'{VPS_DIR}/debian/phaze-vpn/DEBIAN/control'),
        ]
        
        for local_file, remote_file in files_to_deploy:
            local_path = LOCAL_DIR / local_file
            if local_path.exists():
                # Create remote directory if needed
                remote_dir = '/'.join(remote_file.split('/')[:-1])
                stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
                stdout.read()  # Wait for completion
                
                sftp.put(str(local_path), remote_file)
                sftp.chmod(remote_file, 0o644)
                print(f"  ✅ Deployed {local_file}")
            else:
                print(f"  ⚠️  {local_file} not found")
        
        sftp.close()
        print()
        
        # Step 2: Build package on VPS
        print("[2/4] Building package on VPS...")
        build_cmd = f"""
cd {VPS_DIR}

# Check if build tools are available
if ! command -v dpkg-buildpackage &> /dev/null; then
    echo "Installing build tools..."
    apt-get update -qq
    apt-get install -y -qq build-essential devscripts debhelper dpkg-dev
fi

# Make sure build script is executable
chmod +x build-deb.sh 2>/dev/null || true

# Build the package
echo "Building package..."
if [ -f build-deb.sh ]; then
    ./build-deb.sh
else
    # Manual build if script doesn't exist
    dpkg-buildpackage -us -uc -b -d
fi

# Check if build succeeded
if [ -f ../phaze-vpn_*.deb ]; then
    PACKAGE=$(ls -t ../phaze-vpn_*.deb | head -1)
    echo "✅ Package built: $PACKAGE"
    ls -lh "$PACKAGE"
else
    echo "❌ Build failed - no package file found"
    exit 1
fi
"""
        
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors and "error" in errors.lower():
            print(f"⚠️  Errors: {errors}")
        print()
        
        # Step 3: Update repository on VPS
        print("[3/4] Updating repository on VPS...")
        repo_cmd = f"""
cd {VPS_DIR}

# Find the built package
PACKAGE=$(ls -t ../phaze-vpn_*.deb | head -1)
if [ -z "$PACKAGE" ]; then
    echo "❌ Package not found"
    exit 1
fi

REPO_DIR="/opt/phazevpn-repo"

# Ensure repo directory exists
mkdir -p "$REPO_DIR"

# Copy package to repo
cp "$PACKAGE" "$REPO_DIR/"
echo "✅ Package copied to repository"

# Update repository index
cd "$REPO_DIR"
dpkg-scanpackages . /dev/null > Packages 2>/dev/null
gzip -k -f Packages
echo "✅ Repository index updated"

# Create Release file
cat > Release << 'RELEASEEOF'
Architectures: all
Date: $(date -R)
Description: PhazeVPN Local Repository
Label: PhazeVPN
Origin: PhazeVPN
Suite: stable
Version: 1.0
RELEASEEOF

# Add hashes
echo "MD5Sum:" >> Release
for file in Packages Packages.gz; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file")
        md5=$(md5sum "$file" | cut -d' ' -f1)
        echo " $md5 $size $file" >> Release
    fi
done

echo "SHA256:" >> Release
for file in Packages Packages.gz; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file")
        sha256=$(sha256sum "$file" | cut -d' ' -f1)
        echo " $sha256 $size $file" >> Release
    fi
done

echo "✅ Release file created"

# List packages in repo
echo ""
echo "Packages in repository:"
ls -lh "$REPO_DIR"/*.deb 2>/dev/null | tail -5
"""
        
        stdin, stdout, stderr = ssh.exec_command(repo_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors and "error" in errors.lower():
            print(f"⚠️  Errors: {errors}")
        print()
        
        # Step 4: Verify repository setup
        print("[4/4] Verifying repository setup...")
        verify_cmd = f"""
# Check if repo is in apt sources
if grep -q "phazevpn-repo" /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null; then
    echo "✅ Repository is configured in apt sources"
else
    echo "⚠️  Repository not in apt sources"
    echo "   Add with: echo 'deb [trusted=yes] file:///opt/phazevpn-repo ./' | sudo tee -a /etc/apt/sources.list.d/phazevpn.list"
fi

# Test apt update
echo ""
echo "Testing apt update..."
apt-get update -qq 2>&1 | grep -i phazevpn || echo "  (no phazevpn updates found)"

echo ""
echo "✅ Repository ready!"
"""
        
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        print("="*60)
        print("✅ UPDATE DEPLOYED TO VPS!")
        print("="*60)
        print()
        print("To install/upgrade on VPS:")
        print("  sudo apt update")
        print("  sudo apt upgrade phaze-vpn")
        print()
        print("Or install directly:")
        print(f"  sudo dpkg -i {VPS_DIR}/../phaze-vpn_*.deb")
        print("  sudo apt-get install -f")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

