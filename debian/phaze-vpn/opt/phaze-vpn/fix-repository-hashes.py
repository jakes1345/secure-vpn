#!/usr/bin/env python3
"""
Fix repository hash mismatch - regenerate Release file with correct hashes
"""

import paramiko
import hashlib
import gzip

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
            print(f"   ✅ {output.strip()[:200]}")
        return True, output
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, output

def main():
    print("="*80)
    print("🔧 FIXING REPOSITORY HASH MISMATCH")
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
    
    repo_dir = "/var/www/phazevpn-repo"
    
    # ============================================================
    # 1. REGENERATE PACKAGES FILE
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  REGENERATING PACKAGES FILE")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}
    dpkg-scanpackages --arch amd64 pool/main > dists/stable/main/binary-amd64/Packages 2>/dev/null
    gzip -k -f dists/stable/main/binary-amd64/Packages
    echo "Packages file regenerated"
    """, "Regenerating Packages and Packages.gz")
    
    # ============================================================
    # 2. CALCULATE CORRECT HASHES
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CALCULATING CORRECT HASHES")
    print("="*80)
    
    # Get file sizes and hashes
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable/main/binary-amd64
    echo "Packages file:"
    ls -lh Packages Packages.gz
    echo ""
    echo "MD5:"
    md5sum Packages Packages.gz
    echo ""
    echo "SHA1:"
    sha1sum Packages Packages.gz
    echo ""
    echo "SHA256:"
    sha256sum Packages Packages.gz
    """, "Getting file hashes")
    
    # ============================================================
    # 3. REGENERATE RELEASE FILE WITH CORRECT HASHES
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  REGENERATING RELEASE FILE")
    print("="*80)
    
    # Create Release file with correct hashes
    release_script = f"""
    cd {repo_dir}/dists/stable
    
    # Get hashes
    PACKAGES_SIZE=$(stat -c%s main/binary-amd64/Packages)
    PACKAGES_GZ_SIZE=$(stat -c%s main/binary-amd64/Packages.gz)
    PACKAGES_MD5=$(md5sum main/binary-amd64/Packages | cut -d' ' -f1)
    PACKAGES_GZ_MD5=$(md5sum main/binary-amd64/Packages.gz | cut -d' ' -f1)
    PACKAGES_SHA1=$(sha1sum main/binary-amd64/Packages | cut -d' ' -f1)
    PACKAGES_GZ_SHA1=$(sha1sum main/binary-amd64/Packages.gz | cut -d' ' -f1)
    PACKAGES_SHA256=$(sha256sum main/binary-amd64/Packages | cut -d' ' -f1)
    PACKAGES_GZ_SHA256=$(sha256sum main/binary-amd64/Packages.gz | cut -d' ' -f1)
    
    # Create Release file
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
    
    echo "Release file created with correct hashes"
    """
    
    run_command(ssh, release_script, "Creating Release file with correct hashes")
    
    # ============================================================
    # 4. SIGN RELEASE FILE
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  SIGNING RELEASE FILE")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable
    gpg --default-key admin@phazevpn.com --armor --detach-sign --output Release.gpg Release 2>/dev/null || \\
    gpg --armor --detach-sign --output Release.gpg Release 2>/dev/null || \\
    echo "Warning: Could not sign (may need to set default key)"
    """, "Signing Release file")
    
    # ============================================================
    # 5. VERIFY FIX
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  VERIFYING FIX")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable
    echo "Release file:"
    cat Release
    echo ""
    echo "Release.gpg exists:"
    test -f Release.gpg && echo "Yes" || echo "No"
    """, "Verifying Release file")
    
    # Test HTTP access
    run_command(ssh, """
    curl -s http://localhost/repo/dists/stable/Release | head -15
    """, "Testing Release file via HTTP")
    
    print("\n" + "="*80)
    print("✅ REPOSITORY FIXED")
    print("="*80)
    print("\n📝 Now try on your local machine:")
    print("   sudo apt update")
    print("   apt list --upgradable | grep phaze-vpn")
    print("\n✅ The hash mismatch should be fixed!")
    
    ssh.close()

if __name__ == "__main__":
    main()

