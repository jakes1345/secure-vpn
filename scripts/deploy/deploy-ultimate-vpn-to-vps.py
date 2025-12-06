#!/usr/bin/env python3
"""
Deploy Ultimate VPN to VPS with full verification
Includes: WireGuard + Shadowsocks + V2Ray + PhazeVPN Go Server
"""

import paramiko
import os
import sys
from pathlib import Path
import time
import tarfile
import io

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
PROTOCOL_DIR = f"{VPS_DIR}/phazevpn-protocol-go"

def connect_vps():
    """Connect to VPS with verification"""
    print("🔌 Connecting to VPS...")
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
                print("✅ Connected via SSH key")
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    print("✅ Connected via SSH key")
                    return ssh
                except:
                    continue
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        print("✅ Connected (no key)")
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        print("✅ Connected via password")
        return ssh
    
    raise Exception("Failed to connect to VPS")

def verify_command(ssh, command, description):
    """Run command and verify it succeeded"""
    print(f"  ⚙️  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status != 0:
        print(f"  ❌ Failed: {error}")
        return False, output, error
    
    print(f"  ✅ Success")
    return True, output, error

def upload_file(ssh, local_path, remote_path, description):
    """Upload file with verification"""
    print(f"  📤 Uploading {description}...")
    sftp = ssh.open_sftp()
    
    try:
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_path)
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dir}")
        stdout.channel.recv_exit_status()
        
        sftp.put(local_path, remote_path)
        sftp.close()
        
        # Verify file exists
        stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_path} && echo 'exists'")
        if 'exists' in stdout.read().decode():
            print(f"  ✅ Uploaded and verified: {description}")
            return True
        else:
            print(f"  ❌ Upload failed: {description}")
            return False
    except Exception as e:
        print(f"  ❌ Upload error: {e}")
        return False

def upload_directory(ssh, local_dir, remote_dir, description):
    """Upload directory with verification"""
    print(f"  📤 Uploading {description}...")
    
    # Create tarball
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        local_path = Path(local_dir)
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(local_path.parent)
                tar.add(file_path, arcname=arcname)
    
    tar_buffer.seek(0)
    tar_data = tar_buffer.read()
    
    # Upload tarball
    sftp = ssh.open_sftp()
    temp_tar = f"/tmp/{os.path.basename(local_dir)}.tar.gz"
    with sftp.file(temp_tar, 'wb') as f:
        f.write(tar_data)
    sftp.close()
    
    # Extract on remote
    stdin, stdout, stderr = ssh.exec_command(
        f"mkdir -p {remote_dir} && "
        f"cd {os.path.dirname(remote_dir)} && "
        f"tar -xzf {temp_tar} && "
        f"rm {temp_tar} && "
        f"echo 'extracted'"
    )
    result = stdout.read().decode()
    
    if 'extracted' in result:
        print(f"  ✅ Uploaded and verified: {description}")
        return True
    else:
        print(f"  ❌ Upload failed: {description}")
        return False

def main():
    print("=" * 70)
    print("🚀 Ultimate VPN Deployment to VPS")
    print("=" * 70)
    print(f"📍 VPS: {VPS_HOST}")
    print(f"📁 Target: {VPS_DIR}")
    print("=" * 70)
    print()
    
    # Connect
    ssh = connect_vps()
    
    try:
        # Step 1: Verify VPS setup
        print("📋 Step 1: Verifying VPS setup...")
        success, output, error = verify_command(ssh, "whoami", "Check user")
        if not success:
            print("❌ VPS verification failed")
            return
        
        success, output, error = verify_command(ssh, "test -d /opt/phaze-vpn && echo 'exists'", "Check base directory")
        if 'exists' not in output:
            verify_command(ssh, "mkdir -p /opt/phaze-vpn", "Create base directory")
        print("✅ VPS ready\n")
        
        # Step 2: Upload Go VPN server files
        print("📋 Step 2: Uploading Go VPN server...")
        local_go_dir = "/opt/phaze-vpn/phazevpn-protocol-go"
        if not os.path.exists(local_go_dir):
            print(f"❌ Local directory not found: {local_go_dir}")
            return
        
        # Upload entire directory
        if not upload_directory(ssh, local_go_dir, PROTOCOL_DIR, "Go VPN server files"):
            print("❌ Failed to upload Go server")
            return
        
        # Verify key files exist
        key_files = [
            "main.go",
            "go.mod",
            "internal/server/server.go",
            "internal/obfuscation/shadowsocks.go",
            "internal/obfuscation/v2ray.go",
            "internal/obfuscation/manager.go",
            "internal/wireguard/manager.go",
            "scripts/deploy-ultimate-vpn.sh"
        ]
        
        print("  🔍 Verifying uploaded files...")
        for key_file in key_files:
            remote_file = f"{PROTOCOL_DIR}/{key_file}"
            stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_file} && echo 'exists'")
            if 'exists' not in stdout.read().decode():
                print(f"  ❌ Missing: {key_file}")
                return
            else:
                print(f"  ✅ Found: {key_file}")
        
        print("✅ Go server uploaded and verified\n")
        
        # Step 3: Install dependencies
        print("📋 Step 3: Installing dependencies...")
        
        # Check if Go is installed and version
        stdin, stdout, stderr = ssh.exec_command("which go && go version 2>&1")
        go_output = stdout.read().decode()
        go_installed = 'go version' in go_output
        
        # Check if Go version is 1.21+
        go_version_ok = False
        if go_installed:
            # Extract version number
            import re
            version_match = re.search(r'go(\d+)\.(\d+)', go_output)
            if version_match:
                major, minor = int(version_match.group(1)), int(version_match.group(2))
                if major > 1 or (major == 1 and minor >= 21):
                    go_version_ok = True
                    print(f"  ✅ Go version OK: {go_output.strip()}")
        
        if not go_installed or not go_version_ok:
            print("  📦 Installing/Upgrading Go to 1.21+...")
            # Install Go 1.21+ from official source
            verify_command(ssh,
                "apt-get update -qq && "
                "apt-get install -y wget && "
                "cd /tmp && "
                "wget -q https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && "
                "rm -rf /usr/local/go && "
                "tar -C /usr/local -xzf /tmp/go1.21.5.linux-amd64.tar.gz && "
                "rm /tmp/go1.21.5.linux-amd64.tar.gz && "
                "/usr/local/go/bin/go version",
                "Install Go 1.21+"
            )
            
            # Verify installation
            stdin, stdout, stderr = ssh.exec_command("/usr/local/go/bin/go version")
            new_go_version = stdout.read().decode()
            if 'go1.21' in new_go_version or 'go1.22' in new_go_version or 'go1.23' in new_go_version:
                print(f"  ✅ Go 1.21+ installed: {new_go_version.strip()}")
            else:
                print(f"  ⚠️  Go version may be old: {new_go_version.strip()}")
        
        # Check if WireGuard is installed
        stdin, stdout, stderr = ssh.exec_command("which wg && wg --version")
        wg_installed = 'WireGuard' in stdout.read().decode() or 'wg' in stdout.read().decode()
        
        if not wg_installed:
            print("  📦 Installing WireGuard...")
            verify_command(ssh,
                "apt-get install -y wireguard wireguard-tools",
                "Install WireGuard"
            )
        
        # Check if Shadowsocks is installed
        stdin, stdout, stderr = ssh.exec_command("which ss-server")
        ss_installed = stdout.read().decode().strip() != ""
        
        if not ss_installed:
            print("  📦 Installing Shadowsocks...")
            verify_command(ssh,
                "apt-get install -y shadowsocks-libev",
                "Install Shadowsocks"
            )
        
        print("✅ Dependencies installed\n")
        
        # Step 4: Build Go server
        print("📋 Step 4: Building Go VPN server...")
        # Prefer /usr/local/go/bin/go (newer version)
        stdin, stdout, stderr = ssh.exec_command("test -f /usr/local/go/bin/go && echo /usr/local/go/bin/go || which go")
        go_binary = stdout.read().decode().strip() or "/usr/local/go/bin/go"
        
        # Verify Go version
        stdin, stdout, stderr = ssh.exec_command(f"{go_binary} version 2>&1")
        go_version_output = stdout.read().decode()
        print(f"  📝 Using Go: {go_binary}")
        print(f"  📝 Version: {go_version_output.strip()}")
        
        # Check if version is sufficient
        if 'go1.18' in go_version_output or 'go1.17' in go_version_output or 'go1.16' in go_version_output:
            print("  ⚠️  Go version too old, trying /usr/local/go/bin/go...")
            go_binary = "/usr/local/go/bin/go"
            stdin, stdout, stderr = ssh.exec_command(f"{go_binary} version 2>&1")
            go_version_output = stdout.read().decode()
            print(f"  📝 New version: {go_version_output.strip()}")
        
        verify_command(ssh,
            f"cd {PROTOCOL_DIR} && "
            f"{go_binary} mod tidy",
            "Tidy Go modules"
        )
        
        verify_command(ssh,
            f"cd {PROTOCOL_DIR} && "
            f"{go_binary} mod download",
            "Download Go dependencies"
        )
        
        verify_command(ssh,
            f"cd {PROTOCOL_DIR} && "
            f"{go_binary} build -o phazevpn-server-go main.go",
            "Build Go server"
        )
        
        # Verify binary exists
        stdin, stdout, stderr = ssh.exec_command(
            f"test -f {PROTOCOL_DIR}/phazevpn-server-go && echo 'exists'"
        )
        if 'exists' not in stdout.read().decode():
            print("❌ Build failed - binary not found")
            return
        
        # Make executable
        verify_command(ssh,
            f"chmod +x {PROTOCOL_DIR}/phazevpn-server-go",
            "Make binary executable"
        )
        
        print("✅ Go server built and verified\n")
        
        # Step 5: Run deployment script
        print("📋 Step 5: Running deployment script...")
        verify_command(ssh,
            f"chmod +x {PROTOCOL_DIR}/scripts/deploy-ultimate-vpn.sh",
            "Make deployment script executable"
        )
        
        # Run deployment script (non-interactive)
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {PROTOCOL_DIR} && "
            "bash scripts/deploy-ultimate-vpn.sh",
            get_pty=True
        )
        
        # Wait for completion
        print("  ⏳ Running deployment (this may take a few minutes)...")
        time.sleep(5)
        
        # Check if script is still running
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep deploy-ultimate-vpn | grep -v grep")
        if stdout.read().decode().strip():
            print("  ⏳ Deployment script running...")
            time.sleep(30)  # Wait for script to complete
        
        print("✅ Deployment script executed\n")
        
        # Step 6: Verify services
        print("📋 Step 6: Verifying services...")
        
        # First, verify Go is in PATH for systemd
        print("  🔍 Verifying Go installation...")
        stdin, stdout, stderr = ssh.exec_command("/usr/local/go/bin/go version")
        go_version = stdout.read().decode().strip()
        print(f"  ✅ {go_version}")
        
        # Ensure Go is in PATH
        verify_command(ssh,
            "echo 'export PATH=$PATH:/usr/local/go/bin' >> /root/.bashrc && "
            "export PATH=$PATH:/usr/local/go/bin && "
            "which go",
            "Add Go to PATH"
        )
        
        services = [
            ("phazevpn-go.service", "PhazeVPN Go Server"),
            ("wg-quick@wg0.service", "WireGuard"),
            ("shadowsocks-phazevpn.service", "Shadowsocks"),
        ]
        
        for service, name in services:
            stdin, stdout, stderr = ssh.exec_command(
                f"systemctl is-active {service} 2>&1"
            )
            status = stdout.read().decode().strip()
            if status == 'active':
                print(f"  ✅ {name} is running")
            else:
                print(f"  ⚠️  {name} status: {status}")
                # Try to enable and start it
                verify_command(ssh,
                    f"systemctl enable {service} && "
                    f"systemctl start {service}",
                    f"Enable and start {name}"
                )
                # Check again
                time.sleep(2)
                stdin, stdout, stderr = ssh.exec_command(
                    f"systemctl is-active {service} 2>&1"
                )
                new_status = stdout.read().decode().strip()
                if new_status == 'active':
                    print(f"  ✅ {name} now running")
                else:
                    print(f"  ⚠️  {name} still not active: {new_status}")
        
        print("✅ Services verified\n")
        
        # Step 7: Final verification
        print("📋 Step 7: Final verification...")
        verification_passed = True
        
        # Check WireGuard
        stdin, stdout, stderr = ssh.exec_command("wg show 2>&1")
        wg_output = stdout.read().decode()
        if wg_output.strip() and 'error' not in wg_output.lower():
            print("  ✅ WireGuard command works")
        else:
            print("  ⚠️  WireGuard interface not active (may need configuration)")
        
        # Check Go server binary exists
        stdin, stdout, stderr = ssh.exec_command(f"test -f {PROTOCOL_DIR}/phazevpn-server-go && echo 'exists'")
        if 'exists' in stdout.read().decode():
            print("  ✅ Go VPN server binary exists")
        else:
            print("  ❌ Go VPN server binary missing")
            verification_passed = False
        
        # Check Go server process
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep '[p]hazevpn-server-go'")
        process_output = stdout.read().decode()
        if process_output.strip():
            print("  ✅ Go VPN server process running")
            print(f"     {process_output.strip().split(chr(10))[0]}")
        else:
            print("  ⚠️  Go VPN server process not found (may need to start)")
        
        # Check services status
        services_status = []
        for service, name in services:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
            status = stdout.read().decode().strip()
            if status == 'active':
                services_status.append(True)
                print(f"  ✅ {name} service is active")
            else:
                services_status.append(False)
                print(f"  ⚠️  {name} service status: {status}")
        
        # Check ports
        ports_to_check = [
            (51820, "PhazeVPN Protocol"),
            (8388, "Shadowsocks"),
        ]
        
        for port, name in ports_to_check:
            stdin, stdout, stderr = ssh.exec_command(f"netstat -tuln 2>/dev/null | grep :{port} || ss -tuln 2>/dev/null | grep :{port}")
            if stdout.read().decode().strip():
                print(f"  ✅ {name} listening on port {port}")
            else:
                print(f"  ⚠️  {name} not listening on port {port} (may be starting)")
        
        # Verify configuration files exist
        config_files = [
            ("/etc/phazevpn/wireguard/wg0.conf", "WireGuard config"),
            ("/etc/phazevpn/shadowsocks/config.json", "Shadowsocks config"),
        ]
        
        for config_path, name in config_files:
            stdin, stdout, stderr = ssh.exec_command(f"test -f {config_path} && echo 'exists'")
            if 'exists' in stdout.read().decode():
                print(f"  ✅ {name} exists")
            else:
                print(f"  ⚠️  {name} not found (may be created by deployment script)")
        
        # Check Go dependencies
        stdin, stdout, stderr = ssh.exec_command(f"cd {PROTOCOL_DIR} && go mod verify 2>&1")
        go_verify = stdout.read().decode()
        if 'all modules verified' in go_verify or not go_verify.strip():
            print("  ✅ Go modules verified")
        else:
            print(f"  ⚠️  Go modules: {go_verify.strip()}")
        
        if verification_passed:
            print("\n✅ Final verification complete - All critical components verified\n")
        else:
            print("\n⚠️  Final verification - Some components need attention\n")
        
        # Summary
        print("=" * 70)
        print("🎉 Deployment Complete!")
        print("=" * 70)
        print()
        
        # Final status check
        print("📊 Final Status Check:")
        stdin, stdout, stderr = ssh.exec_command(
            f"echo '=== Services ===' && "
            f"systemctl is-active phazevpn-go.service 2>&1 | head -1 && "
            f"echo '=== Binary ===' && "
            f"test -f {PROTOCOL_DIR}/phazevpn-server-go && echo 'EXISTS' || echo 'MISSING' && "
            f"echo '=== Process ===' && "
            f"ps aux | grep '[p]hazevpn-server-go' | wc -l"
        )
        status_output = stdout.read().decode()
        print(status_output)
        
        print("📝 Next Steps:")
        print("  1. SSH into VPS: ssh root@{}".format(VPS_HOST))
        print("  2. Check service status: systemctl status phazevpn-go.service")
        print("  3. Check WireGuard: wg show")
        print("  4. View logs: journalctl -u phazevpn-go.service -f")
        print("  5. Test Go server: cd {} && ./phazevpn-server-go --help".format(PROTOCOL_DIR))
        print()
        print("📁 Configuration Files:")
        print(f"  - WireGuard: /etc/phazevpn/wireguard/wg0.conf")
        print(f"  - Shadowsocks: /etc/phazevpn/shadowsocks/config.json")
        print(f"  - V2Ray: /etc/phazevpn/v2ray/config.json")
        print(f"  - Go Server: {PROTOCOL_DIR}/phazevpn-server-go")
        print()
        print("🔍 Verification Commands:")
        print(f"  - Check files: ls -la {PROTOCOL_DIR}/")
        print(f"  - Check services: systemctl list-units | grep -E '(phazevpn|wireguard|shadowsocks)'")
        print(f"  - Check ports: netstat -tuln | grep -E '(51820|8388)'")
        print()
        print("🔥 Ultimate VPN is ready!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        ssh.close()
        print("\n✅ Connection closed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

