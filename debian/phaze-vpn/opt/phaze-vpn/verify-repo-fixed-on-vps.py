#!/usr/bin/env python3
"""
Verify repository is actually fixed on VPS
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
    
    print(output)
    if error and exit_status != 0:
        print(f"Error: {error}")
    return exit_status == 0, output

def main():
    print("="*80)
    print("🔍 VERIFYING REPOSITORY IS FIXED ON VPS")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected to VPS!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    repo_dir = "/var/www/phazevpn-repo"
    
    # Check Packages.gz file size
    print("\n" + "="*80)
    print("1️⃣  CHECKING PACKAGES.GZ FILE")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable/main/binary-amd64
    echo "File sizes:"
    ls -lh Packages Packages.gz
    echo ""
    echo "Actual file size:"
    stat -c%s Packages.gz
    """, "Checking Packages.gz")
    
    # Check Release file hashes
    print("\n" + "="*80)
    print("2️⃣  CHECKING RELEASE FILE HASHES")
    print("="*80)
    
    run_command(ssh, f"""
    cd {repo_dir}/dists/stable/main/binary-amd64
    echo "Calculating current hashes:"
    echo "MD5:"
    md5sum Packages.gz
    echo "SHA1:"
    sha1sum Packages.gz
    echo "SHA256:"
    sha256sum Packages.gz
    echo ""
    echo "What Release file says:"
    grep -A 3 "Packages.gz" ../Release
    """, "Comparing hashes")
    
    # Test apt can read it (simulate user)
    print("\n" + "="*80)
    print("3️⃣  TESTING APT CAN READ IT")
    print("="*80)
    
    run_command(ssh, """
    # Setup test
    curl -fsSL http://localhost/repo/KEY.gpg | gpg --dearmor -o /tmp/test-keyring.gpg 2>&1
    echo "deb [signed-by=/tmp/test-keyring.gpg] http://localhost/repo stable main" > /tmp/test-sources.list
    
    # Try apt update
    apt-cache -o Dir::Etc::sourcelist=/tmp/test-sources.list -o Dir::Etc::sourceparts=- update 2>&1 | head -10
    """, "Testing apt update")
    
    # Check if package is visible
    print("\n" + "="*80)
    print("4️⃣  CHECKING PACKAGE IS VISIBLE")
    print("="*80)
    
    run_command(ssh, """
    apt-cache -o Dir::Etc::sourcelist=/tmp/test-sources.list -o Dir::Etc::sourceparts=- show phaze-vpn 2>&1 | grep -E "^Package:|^Version:" | head -2
    """, "Checking package info")
    
    # Cleanup
    ssh.exec_command("rm -f /tmp/test-keyring.gpg /tmp/test-sources.list")
    
    # Final check - HTTP access
    print("\n" + "="*80)
    print("5️⃣  TESTING HTTP ACCESS")
    print("="*80)
    
    run_command(ssh, """
    echo "Testing Release file:"
    curl -s http://localhost/repo/dists/stable/Release | head -20
    echo ""
    echo "Testing Packages.gz:"
    curl -s -I http://localhost/repo/dists/stable/main/binary-amd64/Packages.gz | grep -E "HTTP|Content-Length"
    """, "Testing HTTP access")
    
    print("\n" + "="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80)
    print("\n📝 If hashes match, the repository is fixed!")
    print("   Try on your machine: sudo apt update")
    
    ssh.close()

if __name__ == "__main__":
    main()

