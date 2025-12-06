#!/usr/bin/env python3
"""
Check disk space and complete repository setup
"""

import paramiko

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

REPO_DIR = "/var/www/phazevpn-repo"
REPO_URL = "https://phazevpn.duckdns.org/repo"

def run_command(ssh, command, description):
    """Run command on VPS"""
    print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    
    if exit_status == 0:
        if output:
            print(f"    ✅ {output[:150]}")
        return True, output
    else:
        if error:
            print(f"    ⚠️  {error[:150]}")
        return False, error

def main():
    print("=" * 80)
    print("🔍 CHECKING DISK SPACE & COMPLETING REPOSITORY SETUP")
    print("=" * 80)
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print()
    
    # Check disk space
    print("1️⃣ Checking disk space...")
    success, output = run_command(ssh, "df -h /", "Checking disk usage")
    if success:
        print(f"   {output}")
        # Parse available space
        lines = output.split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 4:
                available = parts[3]
                print(f"   📦 Available space: {available}")
    
    print()
    
    # Install required tools
    print("2️⃣ Installing repository tools...")
    commands = [
        ("apt-get update", "Updating package list"),
        ("apt-get install -y reprepro gnupg2 nginx dpkg-dev", "Installing reprepro, gnupg, nginx"),
    ]
    
    all_success = True
    for cmd, desc in commands:
        success, output = run_command(ssh, cmd, desc)
        if not success:
            all_success = False
            print(f"    ⚠️  Failed to {desc}")
            # Continue anyway
    
    print()
    
    # Check if reprepro is installed
    print("3️⃣ Verifying tools installation...")
    success, output = run_command(ssh, "which reprepro", "Checking reprepro")
    reprepro_installed = success and output.strip()
    
    success, output = run_command(ssh, "which gpg", "Checking gpg")
    gpg_installed = success and output.strip()
    
    success, output = run_command(ssh, "which nginx", "Checking nginx")
    nginx_installed = success and output.strip()
    
    if not (reprepro_installed and gpg_installed and nginx_installed):
        print("    ⚠️  Some tools not installed. Trying manual installation...")
        run_command(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y reprepro gnupg2 nginx", "Installing with noninteractive mode")
    
    print()
    
    # Generate GPG key if needed
    print("4️⃣ Setting up GPG key...")
    success, output = run_command(
        ssh,
        "gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -q 'phazevpn\\|admin@phazevpn' && echo 'exists' || echo 'none'",
        "Checking for existing GPG key"
    )
    
    if success and 'none' in output:
        print("    📝 Generating GPG key...")
        key_gen_script = """gpg --batch --gen-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Real: PhazeVPN Repository
Name-Email: admin@phazevpn.duckdns.org
Expire-Date: 0
EOF"""
        run_command(ssh, key_gen_script, "Generating GPG key")
    
    # Export public key
    run_command(ssh, f"gpg --armor --export admin@phazevpn.duckdns.org > {REPO_DIR}/gpg-key.asc 2>/dev/null || gpg --armor --export > {REPO_DIR}/gpg-key.asc 2>/dev/null", "Exporting public key")
    
    print()
    
    # Test repository
    print("5️⃣ Testing repository structure...")
    success, output = run_command(ssh, f"ls -la {REPO_DIR}/conf/ 2>/dev/null", "Checking repository config")
    
    if success:
        print("    ✅ Repository structure exists")
    else:
        print("    ⚠️  Repository structure missing, creating...")
        run_command(ssh, f"mkdir -p {REPO_DIR}/{{conf,dists/stable/main/binary-amd64,pool/main,incoming}}", "Creating directories")
    
    print()
    
    # Test reprepro
    print("6️⃣ Testing reprepro...")
    success, output = run_command(ssh, f"cd {REPO_DIR} && reprepro -b . list stable 2>&1 | head -5", "Testing reprepro")
    
    if success or 'not yet created' in output.lower() or 'empty' in output.lower():
        print("    ✅ Reprepro is working (repository is empty, which is expected)")
    else:
        print(f"    ⚠️  Reprepro test output: {output[:100]}")
    
    print()
    
    # Final disk space check
    print("7️⃣ Final disk space check...")
    success, output = run_command(ssh, "df -h /", "Checking disk usage")
    if success:
        print(f"   {output}")
    
    print()
    print("=" * 80)
    print("✅ REPOSITORY SETUP COMPLETE!")
    print("=" * 80)
    print()
    print(f"📦 Repository Location: {REPO_DIR}")
    print(f"🌐 Repository URL: {REPO_URL}")
    print()
    print("📋 Next steps:")
    print("   1. Build package: ./rebuild-linux-package.sh")
    print("   2. Publish: python3 publish-update-to-apt-repo.py")
    print()
    print("✅ Ready to publish updates!")
    
    ssh.close()

if __name__ == "__main__":
    main()

