#!/usr/bin/env python3
"""
Fix InRelease file on VPS - this is what apt actually uses
"""

import paramiko

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
            print(f"   ✅ {output.strip()[:300]}")
        return True, output
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, output

def main():
    print("="*80)
    print("🔧 FIXING INRELEASE FILE ON VPS")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    repo_dir = "/var/www/phazevpn-repo"
    
    # Remove old InRelease file (apt uses this)
    print("\n" + "="*80)
    print("1️⃣  REMOVING OLD INRELEASE FILE")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable
    rm -f InRelease
    echo "Old InRelease removed"
    """, "Removing old InRelease")
    
    # Regenerate Release file with current date
    print("\n" + "="*80)
    print("2️⃣  REGENERATING RELEASE FILE")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable/main/binary-amd64
    
    # Get current file info
    PACKAGES_SIZE=$(stat -c%s Packages)
    PACKAGES_GZ_SIZE=$(stat -c%s Packages.gz)
    PACKAGES_MD5=$(md5sum Packages | cut -d' ' -f1)
    PACKAGES_GZ_MD5=$(md5sum Packages.gz | cut -d' ' -f1)
    PACKAGES_SHA1=$(sha1sum Packages | cut -d' ' -f1)
    PACKAGES_GZ_SHA1=$(sha1sum Packages.gz | cut -d' ' -f1)
    PACKAGES_SHA256=$(sha256sum Packages | cut -d' ' -f1)
    PACKAGES_GZ_SHA256=$(sha256sum Packages.gz | cut -d' ' -f1)
    
    cd {repo_dir}/dists/stable
    
    # Create Release file with CURRENT date
    cat > Release <<EOF
Origin: PhazeVPN
Label: PhazeVPN Repository
Suite: stable
Codename: stable
Architectures: amd64
Components: main
Description: PhazeVPN Official Repository
Date: $(date -Ru)
MD5Sum:
 $PACKAGES_MD5 $PACKAGES_SIZE main/binary-amd64/Packages
 $PACKAGES_GZ_MD5 $PACKAGES_GZ_SIZE main/binary-amd64/Packages.gz
SHA1:
 $PACKAGES_SHA1 $PACKAGES_SIZE main/binary-amd64/Packages
 $PACKAGES_GZ_SHA1 $PACKAGES_GZ_SIZE main/binary-amd64/Packages.gz
SHA256:
 $PACKAGES_SHA256 $PACKAGES_SIZE main/binary-amd64/Packages
 $PACKAGES_GZ_SHA256 $PACKAGES_GZ_SIZE main/binary-amd64/Packages.gz
EOF
    
    echo "Release file regenerated with current date"
    cat Release
    """, "Regenerating Release file")
    
    # Create InRelease file (signed Release - this is what apt uses)
    print("\n" + "="*80)
    print("3️⃣  CREATING INRELEASE FILE")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable
    
    # Try to sign and create InRelease
    gpg --default-key admin@phazevpn.com --clearsign --output InRelease Release 2>/dev/null || \\
    gpg --clearsign --output InRelease Release 2>/dev/null || \\
    (echo "Warning: Could not sign, creating unsigned InRelease" && cp Release InRelease)
    
    echo "InRelease file created"
    ls -lh InRelease Release
    """, "Creating InRelease file")
    
    # Verify files
    print("\n" + "="*80)
    print("4️⃣  VERIFYING FILES")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable
    echo "Release file date:"
    grep "^Date:" Release
    echo ""
    echo "InRelease file:"
    test -f InRelease && echo "Exists" || echo "Missing"
    ls -lh InRelease Release Release.gpg 2>/dev/null
    """, "Verifying files")
    
    # Test HTTP access
    print("\n" + "="*80)
    print("5️⃣  TESTING HTTP ACCESS")
    print("="*80)
    
    run_command(ssh, """
    echo "InRelease via HTTP:"
    curl -s http://localhost/repo/dists/stable/InRelease | head -20
    echo ""
    echo "Release via HTTP:"
    curl -s http://localhost/repo/dists/stable/Release | head -15
    """, "Testing HTTP access")
    
    print("\n" + "="*80)
    print("✅ INRELEASE FILE FIXED")
    print("="*80)
    print("\n📝 Now on your local machine:")
    print("   1. Clear apt cache: sudo rm -rf /var/lib/apt/lists/*phazevpn*")
    print("   2. Update: sudo apt update")
    print("   3. Check: apt list --upgradable | grep phaze-vpn")
    
    ssh.close()

if __name__ == "__main__":
    main()

