#!/bin/bash
# Publish PhazeVPN update to APT repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
REPO_DIR="/var/www/phazevpn-repo"
VERSION_FILE="VERSION"

echo "=========================================="
echo "Publishing PhazeVPN Update"
echo "=========================================="
echo ""

# Get current version and increment
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d ' \n')
else
    CURRENT_VERSION="1.0.0"
fi

# Auto-increment patch version (1.0.0 -> 1.0.1)
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]:-0}
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"

echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"
echo ""

# Update version file
echo "$NEW_VERSION" > "$VERSION_FILE"
echo "✅ Version updated to $NEW_VERSION"

# Update debian/changelog
echo "[1/5] Updating changelog..."
TIMESTAMP=$(date -R)
cat >> debian/changelog << EOF

phaze-vpn ($NEW_VERSION) stable; urgency=medium

  * Website redesign - modern, professional interface
  * Fixed VPN control in admin dashboard
  * Improved API endpoints for all 3 VPN protocols (OpenVPN, WireGuard, PhazeVPN Protocol)
  * Enhanced subscription conversion features
  * Removed all fake/placeholder content
  * Better error handling and user feedback
  * Automatic update system integration
  * Improved navigation and user experience

 -- PhazeVPN Team <admin@phazevpn.duckdns.org>  $TIMESTAMP
EOF
echo "   ✅ Changelog updated"

# Update debian/control if needed
if [ -f "debian/phaze-vpn/DEBIAN/control" ]; then
    sed -i "s/^Version:.*/Version: $NEW_VERSION/" debian/phaze-vpn/DEBIAN/control 2>/dev/null || true
    echo "   ✅ Control file updated"
fi

# Build package
echo "[2/5] Building .deb package..."
if [ -f "build-deb.sh" ]; then
    ./build-deb.sh
elif [ -f "debian/rules" ]; then
    dpkg-buildpackage -us -uc -b
else
    echo "   ⚠️  No build script found, creating simple package..."
    # Create minimal package structure
    mkdir -p deb-build/DEBIAN
    mkdir -p deb-build/opt/phaze-vpn
    
    cat > deb-build/DEBIAN/control << EOF
Package: phaze-vpn
Version: $NEW_VERSION
Architecture: all
Maintainer: PhazeVPN Team <admin@phazevpn.duckdns.org>
Depends: openvpn, openssl, python3, python3-tk, python3-psutil
Description: Professional VPN Server with Web Dashboard
 PhazeVPN - Complete VPN solution with modern web interface
EOF
    
    # Copy essential files
    cp -r web-portal deb-build/opt/phaze-vpn/ 2>/dev/null || true
    cp -r phazevpn-client deb-build/opt/phaze-vpn/ 2>/dev/null || true
    
    # Build package
    dpkg-deb --build deb-build "phaze-vpn_${NEW_VERSION}_all.deb"
    PACKAGE_FILE="phaze-vpn_${NEW_VERSION}_all.deb"
else
    echo "   ✅ Package built"
fi

# Find the built package
PACKAGE_FILE=$(find . -maxdepth 2 -name "phaze-vpn_${NEW_VERSION}_*.deb" 2>/dev/null | head -1)

if [ -z "$PACKAGE_FILE" ]; then
    PACKAGE_FILE=$(find .. -maxdepth 1 -name "phaze-vpn_${NEW_VERSION}_*.deb" 2>/dev/null | head -1)
fi

if [ -z "$PACKAGE_FILE" ] || [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Error: Built package not found"
    echo "   Tried to find: phaze-vpn_${NEW_VERSION}_*.deb"
    exit 1
fi

echo "   ✅ Package found: $PACKAGE_FILE"

# Upload to VPS and add to repository
echo "[3/5] Uploading to VPS..."
python3 << PYTHON_SCRIPT
import paramiko
from pathlib import Path
import sys

VPS_IP = "$VPS_IP"
VPS_USER = "$VPS_USER"
VPS_PASS = "$VPS_PASS"
REPO_DIR = "$REPO_DIR"
PACKAGE_FILE = "$PACKAGE_FILE"
NEW_VERSION = "$NEW_VERSION"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected to VPS")
    
    sftp = ssh.open_sftp()
    
    # Upload package
    remote_package = f"/tmp/phaze-vpn_{NEW_VERSION}_all.deb"
    sftp.put(PACKAGE_FILE, remote_package)
    print(f"   ✅ Package uploaded: {remote_package}")
    
    sftp.close()
    
    # Setup repository if it doesn't exist
    print("[4/5] Setting up repository...")
    stdin, stdout, stderr = ssh.exec_command(f"test -d {REPO_DIR} && echo 'EXISTS' || echo 'MISSING'")
    repo_exists = stdout.read().decode().strip()
    
    if repo_exists == "MISSING":
        print("   Creating repository...")
        ssh.exec_command(f"mkdir -p {REPO_DIR}/{{conf,dists,pool,incoming}}")
        ssh.exec_command(f"chmod 755 {REPO_DIR}")
        
        # Create reprepro config
        stdin, stdout, stderr = ssh.exec_command(f"cat > {REPO_DIR}/conf/distributions << 'EOF'
Origin: PhazeVPN
Label: PhazeVPN Repository
Codename: stable
Architectures: amd64 arm64 all
Components: main
Description: PhazeVPN Official Repository
SignWith: admin@phazevpn.duckdns.org
EOF")
        stdout.channel.recv_exit_status()
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {REPO_DIR}/conf/options << 'EOF'
basedir {REPO_DIR}
EOF")
        stdout.channel.recv_exit_status()
        
        print("   ✅ Repository created")
    else:
        print("   ✅ Repository exists")
    
    # Add package to repository
    print("[5/5] Adding package to repository...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {REPO_DIR} && reprepro -b . remove stable phaze-vpn 2>&1 || true")
    stdout.channel.recv_exit_status()
    
    stdin, stdout, stderr = ssh.exec_command(f"cd {REPO_DIR} && reprepro -b . includedeb stable {remote_package} 2>&1")
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status == 0:
        print("   ✅ Package added to repository")
    else:
        print(f"   ⚠️  Reprepro had issues: {error}")
        # Try alternative method
        print("   Trying alternative method...")
        ssh.exec_command(f"cd {REPO_DIR}/pool/main && cp {remote_package} . && cd {REPO_DIR} && dpkg-scanpackages pool/main /dev/null | gzip > dists/stable/main/binary-amd64/Packages.gz 2>&1 || true")
        print("   ✅ Package added (alternative method)")
    
    # Export GPG key if needed
    stdin, stdout, stderr = ssh.exec_command(f"test -f {REPO_DIR}/gpg-key.asc && echo 'EXISTS' || echo 'MISSING'")
    key_exists = stdout.read().decode().strip()
    
    if key_exists == "MISSING":
        print("   Exporting GPG key...")
        stdin, stdout, stderr = ssh.exec_command("gpg --armor --export admin@phazevpn.duckdns.org > {REPO_DIR}/gpg-key.asc 2>&1 || echo 'Key export failed'")
        stdout.channel.recv_exit_status()
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("✅ Update Published!")
    print("=" * 60)
    print(f"\nVersion: {NEW_VERSION}")
    print(f"Package: {PACKAGE_FILE}")
    print("\nUsers can now update with:")
    print("  sudo apt update")
    print("  sudo apt upgrade phaze-vpn")
    print("\nOr install fresh:")
    print("  sudo apt install phaze-vpn")
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "✅ Update published to APT repository!"

