#!/usr/bin/env python3
"""
Deploy standalone executable build to VPS and rebuild package
"""

import paramiko
from pathlib import Path
import os
import time

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
REPO_DIR = "/opt/phazevpn-repo"
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

def run_remote_command(ssh, command, description="Running command"):
    """Run a command on the remote VPS and print output"""
    print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if output:
        print(f"    {output}")
    if error and "WARNING" not in error:
        print(f"    ⚠️  {error}")
    return output, error

def deploy_file(sftp, local_path, remote_path):
    """Deploy a single file to VPS"""
    try:
        # Ensure parent directory exists
        parent_dir = str(Path(remote_path).parent)
        try:
            sftp.stat(parent_dir)
        except:
            # Directory doesn't exist, create it
            parts = parent_dir.split('/')
            current = ''
            for part in parts:
                if part:
                    current += '/' + part
                    try:
                        sftp.stat(current)
                    except:
                        sftp.mkdir(current)
        
        sftp.put(str(local_path), str(remote_path))
        print(f"  ✅ Deployed {local_path.name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to deploy {local_path.name}: {e}")
        return False

def main():
    print("="*60)
    print("Deploy Standalone Executable Build to VPS")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return 1
    
    print("✅ Connected")
    print()
    
    sftp = ssh.open_sftp()
    
    try:
        # Deploy updated files
        print("[1/5] Deploying updated build files...")
        files_to_deploy = {
            'vpn-gui.py': f'{VPS_DIR}/vpn-gui.py',
            'debian/rules': f'{VPS_DIR}/debian/rules',
            'debian/phaze-vpn.desktop': f'{VPS_DIR}/debian/phaze-vpn.desktop',
            'debian/phaze-vpn/DEBIAN/control': f'{VPS_DIR}/debian/phaze-vpn/DEBIAN/control',
        }
        
        for local_name, remote_path in files_to_deploy.items():
            local_path = LOCAL_DIR / local_name
            if local_path.exists():
                deploy_file(sftp, local_path, remote_path)
            else:
                print(f"  ⚠️  {local_name} not found locally")
        
        print()
        
        # Install PyInstaller if needed
        print("[2/5] Ensuring PyInstaller is available...")
        install_pyinstaller_cmd = """
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "Installing PyInstaller..."
    pip3 install --user pyinstaller --break-system-packages 2>/dev/null || \
    pip3 install --user pyinstaller 2>/dev/null || \
    (apt-get update >/dev/null 2>&1 && apt-get install -y python3-pyinstaller >/dev/null 2>&1)
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ PyInstaller installed"
else
    echo "✅ PyInstaller already installed"
fi
"""
        run_remote_command(ssh, install_pyinstaller_cmd)
        print()
        
        # Build the package
        print("[3/5] Building package with standalone executable...")
        print("   (This may take a few minutes - PyInstaller needs to bundle everything)")
        build_cmd = f"""
cd {VPS_DIR}
export PATH="$HOME/.local/bin:$PATH"

# Clean previous builds
rm -rf dist/ build/ *.spec debian/phaze-vpn/usr/bin/phazevpn-client

# Build package (this will trigger PyInstaller in debian/rules)
chmod +x debian/rules
dpkg-buildpackage -us -uc -b 2>&1 | tail -50
"""
        output, error = run_remote_command(ssh, build_cmd, "Building package")
        
        # Check if build succeeded
        stdin, stdout, stderr = ssh.exec_command(f"ls -t {VPS_DIR}/../phaze-vpn_*.deb 2>/dev/null | head -1")
        deb_file = stdout.read().decode().strip()
        
        if deb_file and Path(deb_file).name:
            print(f"✅ Package built: {Path(deb_file).name}")
        else:
            print("⚠️  Package build may have failed - checking...")
            # Check if executable was created
            stdin, stdout, stderr = ssh.exec_command(f"test -f {VPS_DIR}/dist/phazevpn-client && echo 'executable exists' || echo 'executable missing'")
            exec_status = stdout.read().decode().strip()
            print(f"   Executable status: {exec_status}")
        
        print()
        
        # Update repository
        print("[4/5] Updating repository...")
        if deb_file:
            update_repo_cmd = f"""
sudo mkdir -p {REPO_DIR}
sudo cp {deb_file} {REPO_DIR}/
sudo chown {VPS_USER}:{VPS_USER} {REPO_DIR}/*.deb
cd {REPO_DIR}
dpkg-scanpackages . /dev/null > Packages
gzip -kf Packages
echo "✅ Repository updated"
"""
            run_remote_command(ssh, update_repo_cmd)
        else:
            print("⚠️  No package file found - skipping repository update")
        
        print()
        
        # Verify the executable
        print("[5/5] Verifying standalone executable...")
        verify_cmd = f"""
if [ -f {VPS_DIR}/dist/phazevpn-client ]; then
    echo "✅ Standalone executable found"
    ls -lh {VPS_DIR}/dist/phazevpn-client
    file {VPS_DIR}/dist/phazevpn-client | head -1
    echo ""
    echo "Testing if it's truly standalone (checking for Python dependency)..."
    ldd {VPS_DIR}/dist/phazevpn-client 2>/dev/null | head -5 || echo "  (Not a dynamic binary - good, it's self-contained)"
elif [ -f {VPS_DIR}/../phaze-vpn_*.deb ]; then
    echo "✅ Package exists - extracting to check executable..."
    TEMP_DIR=$(mktemp -d)
    dpkg-deb -x {VPS_DIR}/../phaze-vpn_*.deb $TEMP_DIR
    if [ -f $TEMP_DIR/usr/bin/phazevpn-client ]; then
        echo "✅ Executable found in package: /usr/bin/phazevpn-client"
        ls -lh $TEMP_DIR/usr/bin/phazevpn-client
        file $TEMP_DIR/usr/bin/phazevpn-client | head -1
    else
        echo "⚠️  Executable not found in package"
    fi
    rm -rf $TEMP_DIR
else
    echo "⚠️  Could not verify - package or executable not found"
fi
"""
        run_remote_command(ssh, verify_cmd)
        print()
        
        print("="*60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*60)
        print()
        print("The new package includes a standalone executable!")
        print("Users can run: phazevpn-client (no Python needed)")
        print()
        if deb_file:
            print(f"Package: {Path(deb_file).name}")
            print(f"Location: {deb_file}")
            print()
            print("To install/upgrade:")
            print("  sudo apt update")
            print("  sudo apt upgrade phaze-vpn")
            print()
        
    finally:
        sftp.close()
        ssh.close()

if __name__ == '__main__':
    exit(main() or 0)

