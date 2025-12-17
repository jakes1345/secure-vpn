#!/usr/bin/env python3
"""
Verify APT Repository is Working on VPS
Test that updates will actually show up
"""

import paramiko
import subprocess

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
    print("🔍 VERIFYING APT REPOSITORY ON VPS")
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
    # 1. CHECK REPOSITORY STRUCTURE
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  CHECKING REPOSITORY STRUCTURE")
    print("="*80)
    
    repo_dir = "/var/www/phazevpn-repo"
    
    run_command(ssh, f"ls -lah {repo_dir}/", "Repository directory")
    run_command(ssh, f"ls -lah {repo_dir}/pool/main/", "Package pool")
    run_command(ssh, f"ls -lah {repo_dir}/dists/stable/main/binary-amd64/", "Binary directory")
    
    # ============================================================
    # 2. CHECK PACKAGE EXISTS
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CHECKING PACKAGE IN REPOSITORY")
    print("="*80)
    
    run_command(ssh, f"find {repo_dir} -name '*.deb' -ls", "Finding .deb packages")
    run_command(ssh, f"cat {repo_dir}/dists/stable/main/binary-amd64/Packages | grep -A 5 'Package: phaze-vpn'", 
                "Package metadata")
    
    # ============================================================
    # 3. CHECK REPOSITORY FILES
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  CHECKING REPOSITORY FILES")
    print("="*80)
    
    run_command(ssh, f"cat {repo_dir}/dists/stable/Release", "Release file")
    run_command(ssh, f"test -f {repo_dir}/dists/stable/Release.gpg && echo 'GPG signature exists' || echo 'WARNING: No GPG signature'",
                "GPG signature check")
    run_command(ssh, f"test -f {repo_dir}/KEY.gpg && echo 'Public key exists' || echo 'WARNING: No public key'",
                "Public key check")
    
    # ============================================================
    # 4. TEST REPOSITORY ACCESS (from VPS itself)
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  TESTING REPOSITORY ACCESS")
    print("="*80)
    
    # Test HTTP access
    run_command(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost/repo/dists/stable/Release",
                "HTTP access test")
    run_command(ssh, f"curl -s http://localhost/repo/dists/stable/Release | head -5",
                "Release file via HTTP")
    
    # ============================================================
    # 5. TEST APT CAN READ REPOSITORY
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  TESTING APT CAN READ REPOSITORY")
    print("="*80)
    
    # Create temporary sources list
    test_sources = "/tmp/phazevpn-test.list"
    test_keyring = "/tmp/phazevpn-test-keyring.gpg"
    
    # Download key
    run_command(ssh, f"curl -fsSL http://localhost/repo/KEY.gpg | gpg --dearmor -o {test_keyring} 2>&1",
                "Downloading GPG key")
    
    # Create sources list
    run_command(ssh, f"echo 'deb [signed-by={test_keyring}] http://localhost/repo stable main' > {test_sources}",
                "Creating test sources list")
    
    # Test apt can read it
    run_command(ssh, f"apt-cache -o Dir::Etc::sourcelist={test_sources} -o Dir::Etc::sourceparts=- policy phaze-vpn 2>&1",
                "Testing apt can read repository")
    
    # ============================================================
    # 6. VERIFY PACKAGE VERSION
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  VERIFYING PACKAGE VERSION")
    print("="*80)
    
    run_command(ssh, f"cat {repo_dir}/dists/stable/main/binary-amd64/Packages | grep -E 'Package:|Version:' | head -4",
                "Package version in repository")
    
    # ============================================================
    # 7. TEST FROM EXTERNAL (simulate user)
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  TESTING EXTERNAL ACCESS")
    print("="*80)
    
    # Test from outside (using curl from local machine)
    import requests
    try:
        repo_url = "https://phazevpn.com/repo"
        response = requests.get(f"{repo_url}/dists/stable/Release", verify=False, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Repository accessible from internet")
            print(f"   ✅ Release file: {len(response.text)} bytes")
        else:
            print(f"   ⚠️  HTTP {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Could not test external access: {e}")
    
    # ============================================================
    # 8. CREATE TEST SCRIPT FOR USERS
    # ============================================================
    print("\n" + "="*80)
    print("8️⃣  VERIFYING USER SETUP SCRIPT")
    print("="*80)
    
    run_command(ssh, f"test -f {repo_dir}/setup-repo.sh && echo 'Setup script exists' || echo 'WARNING: Setup script missing'",
                "Setup script check")
    run_command(ssh, f"head -10 {repo_dir}/setup-repo.sh",
                "Setup script preview")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("📊 VERIFICATION SUMMARY")
    print("="*80)
    
    # Check if everything is in place
    checks = {
        "Repository directory": f"test -d {repo_dir}",
        "Package file": f"find {repo_dir} -name 'phaze-vpn_*.deb' | head -1",
        "Packages file": f"test -f {repo_dir}/dists/stable/main/binary-amd64/Packages",
        "Release file": f"test -f {repo_dir}/dists/stable/Release",
        "Public key": f"test -f {repo_dir}/KEY.gpg",
        "Setup script": f"test -f {repo_dir}/setup-repo.sh",
    }
    
    print("\n✅ Repository Status:")
    for check_name, check_cmd in checks.items():
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        if stdout.channel.recv_exit_status() == 0:
            result = stdout.read().decode().strip()
            if result:
                print(f"   ✅ {check_name}: {result}")
            else:
                print(f"   ✅ {check_name}: OK")
        else:
            print(f"   ❌ {check_name}: MISSING")
    
    print("\n" + "="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80)
    print("\n📝 If all checks passed, users can:")
    print("   1. Add repository: curl -fsSL https://phazevpn.com/repo/setup-repo.sh | bash")
    print("   2. Update: sudo apt update")
    print("   3. See update: apt list --upgradable | grep phaze-vpn")
    print("   4. Install: sudo apt upgrade phaze-vpn")
    
    ssh.close()

if __name__ == "__main__":
    main()

