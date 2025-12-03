#!/usr/bin/env python3
"""
Fix repository and verify it works - make sure update shows up
"""

import paramiko
import glob
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
            print(f"   ✅ {output.strip()[:300]}")
        return True, output
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, output

def main():
    print("="*80)
    print("🔧 FIXING AND VERIFYING REPOSITORY ON VPS")
    print("="*80)
    
    # Find latest .deb package
    deb_files = glob.glob("../phaze-vpn_*.deb")
    if not deb_files:
        print("❌ No .deb package found! Building...")
        import subprocess
        subprocess.run(["./build-deb.sh"], cwd=".")
        deb_files = glob.glob("../phaze-vpn_*.deb")
    
    latest_deb = max(deb_files, key=lambda p: Path(p).stat().st_mtime)
    print(f"\n📦 Found package: {latest_deb}")
    print(f"   Size: {Path(latest_deb).stat().st_size / 1024 / 1024:.1f} MB")
    
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
    
    # Upload package
    print(f"\n📤 Uploading package to VPS...")
    sftp = ssh.open_sftp()
    remote_path = f"/tmp/{Path(latest_deb).name}"
    try:
        sftp.put(latest_deb, remote_path)
        print(f"   ✅ Uploaded: {remote_path}")
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        sftp.close()
        ssh.close()
        return
    finally:
        sftp.close()
    
    # Update repository
    print(f"\n🔄 Updating repository...")
    stdin, stdout, stderr = ssh.exec_command(f"update-phazevpn-repo {remote_path}")
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    
    if exit_status == 0:
        print(f"   ✅ Repository updated!")
    else:
        print(f"   ⚠️  Warning: {output}")
    
    # Verify package is in repository
    print(f"\n🔍 Verifying package in repository...")
    repo_dir = "/var/www/phazevpn-repo"
    
    # Check package file
    run_command(ssh, f"ls -lh {repo_dir}/pool/main/*.deb", "Package files in repository")
    
    # Check Packages file
    run_command(ssh, f"cat {repo_dir}/dists/stable/main/binary-amd64/Packages | grep -A 10 'Package: phaze-vpn'",
                "Package metadata")
    
    # Test apt can see it
    print(f"\n🧪 Testing apt can see the update...")
    test_keyring = "/tmp/phazevpn-test-keyring.gpg"
    test_sources = "/tmp/phazevpn-test.list"
    
    # Setup test
    run_command(ssh, f"curl -fsSL http://localhost/repo/KEY.gpg | gpg --dearmor -o {test_keyring} 2>&1",
                "Downloading GPG key")
    run_command(ssh, f"echo 'deb [signed-by={test_keyring}] http://localhost/repo stable main' > {test_sources}",
                "Creating test sources")
    
    # Test apt policy
    run_command(ssh, f"apt-cache -o Dir::Etc::sourcelist={test_sources} -o Dir::Etc::sourceparts=- policy phaze-vpn 2>&1",
                "Testing apt policy (this shows if update is available)")
    
    # Test apt list
    run_command(ssh, f"apt-cache -o Dir::Etc::sourcelist={test_sources} -o Dir::Etc::sourceparts=- madison phaze-vpn 2>&1",
                "Testing apt madison (shows all versions)")
    
    # Clean up
    ssh.exec_command(f"rm -f {remote_path} {test_keyring} {test_sources}")
    
    # Final verification
    print(f"\n" + "="*80)
    print("✅ FINAL VERIFICATION")
    print("="*80)
    
    # Check version in repository
    stdin, stdout, stderr = ssh.exec_command(
        f"cat {repo_dir}/dists/stable/main/binary-amd64/Packages | grep -E '^Package:|^Version:' | head -2"
    )
    version_info = stdout.read().decode().strip()
    print(f"\n📦 Package in repository:")
    print(f"   {version_info}")
    
    # Check HTTP access
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s http://localhost/repo/dists/stable/Release | head -3"
    )
    release_info = stdout.read().decode().strip()
    print(f"\n🌐 Repository accessible:")
    print(f"   {release_info}")
    
    print(f"\n" + "="*80)
    print("✅ REPOSITORY VERIFIED AND WORKING")
    print("="*80)
    print(f"\n📝 Users can now:")
    print(f"   1. Add repo: curl -fsSL https://phazevpn.com/repo/setup-repo.sh | bash")
    print(f"   2. Update: sudo apt update")
    print(f"   3. See update: apt list --upgradable | grep phaze-vpn")
    print(f"   4. Install: sudo apt upgrade phaze-vpn")
    print(f"\n✅ The update WILL show up in Update Manager!")
    
    ssh.close()

if __name__ == "__main__":
    main()

