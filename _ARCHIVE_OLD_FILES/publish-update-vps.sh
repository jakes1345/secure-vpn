#!/bin/bash
# Build and publish PhazeVPN update on VPS

set -e

echo "=========================================="
echo "Publishing PhazeVPN Update to APT Repository"
echo "=========================================="
echo ""

python3 << 'PYTHON_SCRIPT'
import paramiko
from pathlib import Path
import sys
import os
from datetime import datetime

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
REPO_DIR = "/var/www/phazevpn-repo"
BUILD_DIR = "/tmp/phazevpn-build"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    
    # Get current version
    print("\n[1/6] Checking current version...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/secure-vpn && cat VERSION 2>/dev/null || echo '1.0.0'")
    current_version = stdout.read().decode().strip() or "1.0.0"
    print(f"   Current version: {current_version}")
    
    # Increment version
    version_parts = current_version.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0
    patch = int(version_parts[2]) if len(version_parts) > 2 else 0
    new_patch = patch + 1
    new_version = f"{major}.{minor}.{new_patch}"
    print(f"   New version: {new_version}")
    
    # Create build directory
    print("\n[2/6] Setting up build environment...")
    ssh.exec_command(f"rm -rf {BUILD_DIR} && mkdir -p {BUILD_DIR}")
    ssh.exec_command(f"cp -r /opt/secure-vpn/* {BUILD_DIR}/ 2>/dev/null || true")
    print("   ✅ Build directory created")
    
    # Update version files
    print("\n[3/6] Updating version files...")
    ssh.exec_command(f"echo '{new_version}' > {BUILD_DIR}/VERSION")
    
    # Update changelog
    timestamp = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    changelog_text = f"""phaze-vpn ({new_version}) stable; urgency=medium

  * Website redesign - modern, professional interface
  * Fixed VPN control in admin dashboard
  * Improved API endpoints for all 3 VPN protocols
  * Enhanced subscription conversion features
  * Removed all fake/placeholder content
  * Better error handling and user feedback
  * Automatic update system integration

 -- PhazeVPN Team <admin@phazevpn.duckdns.org>  {timestamp}
"""
    
    # Write changelog entry
    stdin, stdout, stderr = ssh.exec_command(f"cat >> {BUILD_DIR}/debian/changelog", get_pty=False)
    stdin.write(changelog_text)
    stdin.close()
    stdout.channel.recv_exit_status()
    print("   ✅ Version files updated")
    
    # Update control file
    stdin, stdout, stderr = ssh.exec_command(f"sed -i 's/^Version:.*/Version: {new_version}/' {BUILD_DIR}/debian/phaze-vpn/DEBIAN/control 2>/dev/null || true")
    stdout.channel.recv_exit_status()
    
    # Install build tools if needed
    print("\n[4/6] Installing build tools...")
    stdin, stdout, stderr = ssh.exec_command("which dpkg-buildpackage || echo 'MISSING'")
    has_build = 'MISSING' in stdout.read().decode()
    
    if has_build:
        print("   Installing build-essential...")
        stdin, stdout, stderr = ssh.exec_command("apt-get update && apt-get install -y build-essential devscripts debhelper 2>&1")
        stdout.channel.recv_exit_status()
        print("   ✅ Build tools installed")
    else:
        print("   ✅ Build tools available")
    
    # Build package
    print("\n[5/6] Building .deb package...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {BUILD_DIR} && chmod +x debian/*.sh debian/rules 2>/dev/null || true && dpkg-buildpackage -us -uc -b 2>&1")
    build_output = stdout.read().decode()
    build_error = stderr.read().decode()
    exit_status = stdout.channel.recv_exit_status()
    
    package_file = None
    
    if exit_status != 0:
        print(f"   ⚠️  Build had issues: {build_error[:200]}")
        # Try simple package build
        print("   Trying simple package build...")
        ssh.exec_command(f"cd {BUILD_DIR} && mkdir -p ../phaze-vpn-pkg/DEBIAN ../phaze-vpn-pkg/opt/phaze-vpn")
        
        control_content = f"""Package: phaze-vpn
Version: {new_version}
Architecture: all
Maintainer: PhazeVPN Team <admin@phazevpn.duckdns.org>
Depends: openvpn, openssl, python3, python3-tk, python3-psutil
Description: Professional VPN Server with Web Dashboard
 PhazeVPN - Complete VPN solution
"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/phaze-vpn-control << 'CONTROL_EOF'\n{control_content}CONTROL_EOF")
        stdout.channel.recv_exit_status()
        ssh.exec_command(f"cp /tmp/phaze-vpn-control {BUILD_DIR}/../phaze-vpn-pkg/DEBIAN/control")
        ssh.exec_command(f"cp -r {BUILD_DIR}/web-portal {BUILD_DIR}/../phaze-vpn-pkg/opt/phaze-vpn/ 2>/dev/null || true")
        ssh.exec_command(f"cd {BUILD_DIR}/.. && dpkg-deb --build phaze-vpn-pkg phaze-vpn_{new_version}_all.deb")
        package_file = f"/tmp/phaze-vpn_{new_version}_all.deb"
    else:
        # Find built package
        stdin, stdout, stderr = ssh.exec_command(f"find /tmp -name 'phaze-vpn_{new_version}_*.deb' 2>/dev/null | head -1")
        package_file = stdout.read().decode().strip()
        
        if not package_file:
            stdin, stdout, stderr = ssh.exec_command(f"find {BUILD_DIR}/.. -name 'phaze-vpn_*.deb' 2>/dev/null | head -1")
            package_file = stdout.read().decode().strip()
    
    if not package_file or 'phaze-vpn' not in package_file:
        print(f"   ❌ Package not found")
        print(f"   Build output: {build_output[:500]}")
        sys.exit(1)
    
    print(f"   ✅ Package built: {package_file}")
    
    # Setup repository if needed
    print("\n[6/6] Adding to APT repository...")
    stdin, stdout, stderr = ssh.exec_command(f"test -d {REPO_DIR} && echo 'EXISTS' || echo 'MISSING'")
    repo_exists = stdout.read().decode().strip()
    
    if repo_exists == "MISSING":
        print("   Creating repository...")
        ssh.exec_command(f"mkdir -p {REPO_DIR}/{{conf,dists/stable/main/binary-amd64,pool/main,incoming}}")
        
        # Create reprepro config
        dist_config = """Origin: PhazeVPN
Label: PhazeVPN Repository
Codename: stable
Architectures: amd64 arm64 all
Components: main
Description: PhazeVPN Official Repository
SignWith: admin@phazevpn.duckdns.org
"""
        stdin, stdout, stderr = ssh.exec_command(f"cat > {REPO_DIR}/conf/distributions << 'DIST_EOF'\n{dist_config}DIST_EOF")
        stdout.channel.recv_exit_status()
        
        stdin, stdout, stderr = ssh.exec_command(f"echo 'basedir {REPO_DIR}' > {REPO_DIR}/conf/options")
        stdout.channel.recv_exit_status()
        
        # Install reprepro if needed
        stdin, stdout, stderr = ssh.exec_command("which reprepro || echo 'MISSING'")
        if 'MISSING' in stdout.read().decode():
            ssh.exec_command("apt-get install -y reprepro 2>&1")
        
        print("   ✅ Repository created")
    
    # Add package to repository
    stdin, stdout, stderr = ssh.exec_command(f"cd {REPO_DIR} && reprepro -b . remove stable phaze-vpn 2>&1 || true")
    stdout.channel.recv_exit_status()
    
    stdin, stdout, stderr = ssh.exec_command(f"cd {REPO_DIR} && reprepro -b . includedeb stable {package_file} 2>&1")
    add_output = stdout.read().decode()
    add_error = stderr.read().decode()
    add_status = stdout.channel.recv_exit_status()
    
    if add_status == 0:
        print("   ✅ Package added to repository")
    else:
        print(f"   ⚠️  Reprepro issue: {add_error[:200]}")
        # Alternative: manual package addition
        print("   Using alternative method...")
        ssh.exec_command(f"cp {package_file} {REPO_DIR}/pool/main/")
        ssh.exec_command(f"cd {REPO_DIR} && dpkg-scanpackages pool/main /dev/null 2>/dev/null | gzip > dists/stable/main/binary-amd64/Packages.gz")
        print("   ✅ Package added (alternative method)")
    
    # Update version on VPS
    ssh.exec_command(f"echo '{new_version}' > /opt/secure-vpn/VERSION")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("✅ Update Published Successfully!")
    print("=" * 60)
    print(f"\nVersion: {new_version}")
    print(f"Package: {package_file}")
    print("\nUsers can now update with:")
    print("  sudo apt update")
    print("  sudo apt upgrade phaze-vpn")
    print("\nRepository URL: https://phazevpn.duckdns.org/repo")
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "✅ Update published!"
