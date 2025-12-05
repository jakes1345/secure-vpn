#!/usr/bin/env python3
"""
Deploy complete updated codebase to VPS and build package there
"""

import paramiko
import os
import tarfile
import io
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

def create_tarball(local_dir, exclude_patterns=None):
    """Create a tarball of the project"""
    if exclude_patterns is None:
        exclude_patterns = ['.git', '__pycache__', '*.pyc', '*.deb', 'node_modules']
    
    tar_buffer = io.BytesIO()
    
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        for item in local_dir.rglob('*'):
            # Skip excluded patterns
            skip = False
            for pattern in exclude_patterns:
                if pattern in str(item):
                    skip = True
                    break
            if skip:
                continue
            
            if item.is_file():
                arcname = item.relative_to(local_dir)
                tar.add(item, arcname=arcname)
    
    tar_buffer.seek(0)
    return tar_buffer.getvalue()

def main():
    print("="*60)
    print("Deploy Complete Update to VPS & Build Package")
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
        # Step 1: Deploy updated files (key files only, not everything)
        print("[1/5] Deploying updated files to VPS...")
        sftp = ssh.open_sftp()
        
        # Deploy key updated files
        files_to_deploy = [
            ('vpn-gui.py', f'{VPS_DIR}/vpn-gui.py'),
            ('vpn-manager.py', f'{VPS_DIR}/vpn-manager.py'),
            ('web-portal/app.py', f'{VPS_DIR}/web-portal/app.py'),
            ('generate-all-configs.py', f'{VPS_DIR}/generate-all-configs.py'),
        ]
        
        for local_file, remote_file in files_to_deploy:
            local_path = LOCAL_DIR / local_file
            if local_path.exists():
                remote_dir = '/'.join(remote_file.split('/')[:-1])
                stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
                stdout.read()
                
                sftp.put(str(local_path), remote_file)
                sftp.chmod(remote_file, 0o755 if local_file.endswith('.py') else 0o644)
                print(f"  ✅ {local_file}")
        
        # Deploy debian directory structure
        print("  Deploying debian directory...")
        debian_files = [
            'debian/changelog',
            'debian/control',
            'debian/rules',
            'debian/compat',
            'debian/phaze-vpn/DEBIAN/control',
        ]
        
        # Also deploy service files if they exist
        service_files = [
            'debian/phaze-vpn.service',
            'debian/phaze-vpn-download.service',
            'debian/phaze-vpn.desktop',
        ]
        debian_files.extend([f for f in service_files if (LOCAL_DIR / f).exists()])
        
        for deb_file in debian_files:
            local_path = LOCAL_DIR / deb_file
            if local_path.exists():
                remote_file = f'{VPS_DIR}/{deb_file}'
                remote_dir = '/'.join(remote_file.split('/')[:-1])
                stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
                stdout.read()
                
                sftp.put(str(local_path), remote_file)
                sftp.chmod(remote_file, 0o644)
                print(f"  ✅ {deb_file}")
        
        sftp.close()
        print()
        
        # Step 2: Build package on VPS
        print("[2/5] Building package on VPS...")
        build_cmd = f"""
cd {VPS_DIR}

# Install build tools if needed
if ! command -v dpkg-buildpackage &> /dev/null; then
    echo "Installing build tools..."
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq build-essential devscripts debhelper dpkg-dev > /dev/null 2>&1
fi

# Ensure debian directory structure exists
mkdir -p debian/phaze-vpn/DEBIAN
mkdir -p debian/phaze-vpn/opt/phaze-vpn
mkdir -p debian/phaze-vpn/etc/systemd/system
mkdir -p debian/phaze-vpn/usr/share/applications

# Copy control file if needed
if [ ! -f debian/control ]; then
    cp debian/phaze-vpn/DEBIAN/control debian/control 2>/dev/null || true
fi

# Make build script executable
chmod +x build-deb.sh 2>/dev/null || true

# Build the package
echo "Building package (this may take a minute)..."
if [ -f build-deb.sh ]; then
    ./build-deb.sh 2>&1 | tail -20
else
    # Manual build
    dpkg-buildpackage -us -uc -b -d 2>&1 | tail -20
fi

# Check result
if ls ../phaze-vpn_*.deb 1> /dev/null 2>&1; then
    PACKAGE=$(ls -t ../phaze-vpn_*.deb | head -1)
    echo ""
    echo "✅ Package built successfully!"
    ls -lh "$PACKAGE"
    echo "$PACKAGE"
else
    echo ""
    echo "❌ Build failed"
    exit 1
fi
"""
        
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if "❌" in output or "error" in errors.lower():
            print(f"⚠️  Build errors: {errors[-500:]}")
            print()
            print("Trying alternative build method...")
            # Try simpler build
            alt_build = f"""
cd {VPS_DIR}
dpkg-buildpackage -us -uc -b 2>&1 | tail -30
"""
            stdin, stdout, stderr = ssh.exec_command(alt_build)
            print(stdout.read().decode())
        print()
        
        # Step 3: Update repository
        print("[3/5] Updating repository on VPS...")
        repo_cmd = f"""
cd {VPS_DIR}

# Find built package
PACKAGE=$(ls -t ../phaze-vpn_*.deb 2>/dev/null | head -1)
if [ -z "$PACKAGE" ]; then
    echo "❌ Package not found"
    exit 1
fi

REPO_DIR="/opt/phazevpn-repo"
mkdir -p "$REPO_DIR"

# Copy to repo
cp "$PACKAGE" "$REPO_DIR/"
echo "✅ Package copied: $(basename $PACKAGE)"

# Update index
cd "$REPO_DIR"
dpkg-scanpackages . /dev/null > Packages 2>/dev/null
gzip -k -f Packages
echo "✅ Repository index updated"

# Create Release
cat > Release << 'EOF'
Architectures: all
Date: $(date -R)
Description: PhazeVPN Repository
Label: PhazeVPN
Origin: PhazeVPN
Suite: stable
Version: 1.0
EOF

echo "MD5Sum:" >> Release
for f in Packages Packages.gz; do
    [ -f "$f" ] && echo " $(md5sum $f | cut -d' ' -f1) $(stat -c%s $f) $f" >> Release
done

echo "SHA256:" >> Release
for f in Packages Packages.gz; do
    [ -f "$f" ] && echo " $(sha256sum $f | cut -d' ' -f1) $(stat -c%s $f) $f" >> Release
done

echo "✅ Release file created"
ls -lh "$REPO_DIR"/*.deb | tail -3
"""
        
        stdin, stdout, stderr = ssh.exec_command(repo_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        # Step 4: Verify
        print("[4/5] Verifying update...")
        verify_cmd = f"""
# Check package version
PACKAGE=$(ls -t /opt/phazevpn-repo/phaze-vpn_*.deb 2>/dev/null | head -1)
if [ -n "$PACKAGE" ]; then
    VERSION=$(dpkg-deb -f "$PACKAGE" Version 2>/dev/null)
    echo "✅ Latest package version: $VERSION"
    echo "✅ Package file: $PACKAGE"
else
    echo "❌ No package found in repository"
fi
"""
        
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        print(stdout.read().decode())
        print()
        
        # Step 5: Instructions
        print("[5/5] Installation instructions...")
        print()
        print("="*60)
        print("✅ UPDATE READY ON VPS!")
        print("="*60)
        print()
        print("To install/upgrade on VPS:")
        print("  sudo apt update")
        print("  sudo apt upgrade phaze-vpn")
        print()
        print("Or install directly:")
        print("  sudo dpkg -i /opt/phazevpn-repo/phaze-vpn_*.deb")
        print("  sudo apt-get install -f")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
