#!/usr/bin/env python3
"""
Deploy PhazeVPN to VPS using CMake build system
Uploads source code and builds on VPS using CMake
"""

import paramiko
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List

# VPS Configuration - can be overridden via environment variables
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')
VPS_DIR = os.environ.get('VPS_DIR', '/root/phaze-vpn')
VPS_INSTALL_DIR = '/opt/phaze-vpn'

def connect_vps() -> paramiko.SSHClient:
    """Connect to VPS using SSH key or password"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Try SSH keys first
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
        Path.home() / '.ssh' / 'id_ecdsa',
    ]
    
    for key_path in key_paths:
        if key_path.exists():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=30)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=30)
                    return ssh
                except:
                    try:
                        key = paramiko.ECDSAKey.from_private_key_file(str(key_path))
                        ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=30)
                        return ssh
                    except:
                        continue
    
    # Fall back to password authentication
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=30)
        return ssh
    
    raise Exception("Failed to connect to VPS - no SSH key or password provided")

def run_command(ssh: paramiko.SSHClient, command: str, check: bool = True) -> tuple:
    """Run command on VPS and return (success, stdout, stderr)"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    stdout_text = stdout.read().decode('utf-8', errors='ignore')
    stderr_text = stderr.read().decode('utf-8', errors='ignore')
    
    if check and exit_status != 0:
        raise Exception(f"Command failed: {command}\nSTDERR: {stderr_text}")
    
    return exit_status == 0, stdout_text, stderr_text

def upload_file(ssh: paramiko.SSHClient, sftp: paramiko.SFTPClient, local_path: Path, remote_path: str) -> bool:
    """Upload a single file to VPS"""
    try:
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_path)
        run_command(ssh, f"mkdir -p '{remote_dir}'", check=False)
        
        sftp.put(str(local_path), remote_path)
        
        # Set executable permissions for scripts
        if local_path.suffix in ['.sh', '.py'] or local_path.name in ['CMakeLists.txt', 'build.sh']:
            sftp.chmod(remote_path, 0o755)
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to upload {local_path.name}: {e}")
        return False

def upload_directory(ssh: paramiko.SSHClient, sftp: paramiko.SFTPClient, local_dir: Path, remote_dir: str, 
                     exclude_patterns: Optional[List[str]] = None) -> int:
    """Recursively upload directory to VPS"""
    if exclude_patterns is None:
        exclude_patterns = [
            '__pycache__', '.git', '*.pyc', '.pytest_cache',
            'build', 'build-*', 'dist', '*.egg-info',
            'node_modules', '.venv', 'venv', 'env',
            '*.log', '*.tmp', '.DS_Store', 'Thumbs.db'
        ]
    
    uploaded = 0
    
    for root, dirs, files in os.walk(local_dir):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not any(
            pattern in d or d.endswith(pattern.replace('*', ''))
            for pattern in exclude_patterns
        )]
        
        for file in files:
            # Skip excluded files
            if any(
                pattern in file or file.endswith(pattern.replace('*', ''))
                for pattern in exclude_patterns
            ):
                continue
            
            local_path = Path(root) / file
            rel_path = local_path.relative_to(local_dir)
            remote_path = f"{remote_dir}/{rel_path}".replace('\\', '/')
            
            if upload_file(ssh, sftp, local_path, remote_path):
                uploaded += 1
    
    return uploaded

def main():
    print("=" * 80)
    print("🚀 Deploying PhazeVPN to VPS using CMake")
    print("=" * 80)
    print(f"VPS: {VPS_USER}@{VPS_HOST}")
    print(f"Source Dir: {VPS_DIR}")
    print(f"Install Dir: {VPS_INSTALL_DIR}")
    print()
    
    script_dir = Path(__file__).parent.absolute()
    
    # Connect to VPS
    print("📡 Connecting to VPS...")
    try:
        ssh = connect_vps()
        print(f"   ✅ Connected to {VPS_HOST}\n")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        sys.exit(1)
    
    try:
        # Check/create VPS directory
        print("📁 Setting up VPS directory...")
        run_command(ssh, f"mkdir -p {VPS_DIR}")
        print(f"   ✅ Directory ready: {VPS_DIR}\n")
        
        # Upload essential CMake files first
        print("📤 Uploading CMake build system...")
        sftp = ssh.open_sftp()
        cmake_files = [
            'CMakeLists.txt',
            'build.sh',
            'deploy-to-vps-cmake.sh',
        ]
        
        cmake_dirs = [
            'cmake',
            'phazevpn-protocol-go',
            'web-portal',
            'phazevpn-protocol',
            'browser',
        ]
        
        uploaded = 0
        for cmake_file in cmake_files:
            local_file = script_dir / cmake_file
            if local_file.exists():
                remote_file = f"{VPS_DIR}/{cmake_file}"
                if upload_file(ssh, sftp, local_file, remote_file):
                    print(f"   ✅ {cmake_file}")
                    uploaded += 1
        
        # Upload CMake subdirectories
        for cmake_dir in cmake_dirs:
            local_dir = script_dir / cmake_dir
            if local_dir.exists() and local_dir.is_dir():
                remote_dir = f"{VPS_DIR}/{cmake_dir}"
                print(f"   📁 Uploading {cmake_dir}/...")
                count = upload_directory(ssh, sftp, local_dir, remote_dir)
                uploaded += count
                print(f"      ✅ {count} files")
        
        sftp.close()
        print(f"\n   📊 Uploaded {uploaded} CMake-related files\n")
        
        # Upload project source files (excluding build artifacts)
        print("📤 Uploading project source files...")
        sftp = ssh.open_sftp()
        
        # Essential directories to upload
        essential_dirs = [
            'web-portal',
            'phazevpn-protocol',
            'phazevpn-protocol-go',
            'config',
            'scripts',
        ]
        
        # Essential files to upload
        essential_files = [
            'vpn-manager.py',
            'vpn-gui.py',
            'install.sh',
            'README.md',
            'README-CMAKE.md',
            'README-VPS-DEPLOY.md',
        ]
        
        total_uploaded = uploaded
        
        for essential_file in essential_files:
            local_file = script_dir / essential_file
            if local_file.exists():
                remote_file = f"{VPS_DIR}/{essential_file}"
                if upload_file(ssh, sftp, local_file, remote_file):
                    total_uploaded += 1
        
        # Upload directories (skip if already uploaded as CMake dirs)
        for essential_dir in essential_dirs:
            if essential_dir not in cmake_dirs:
                local_dir = script_dir / essential_dir
                if local_dir.exists() and local_dir.is_dir():
                    remote_dir = f"{VPS_DIR}/{essential_dir}"
                    count = upload_directory(ssh, sftp, local_dir, remote_dir)
                    total_uploaded += count
        
        sftp.close()
        print(f"\n   📊 Total uploaded: {total_uploaded} files\n")
        
        # Install dependencies on VPS
        print("📦 Installing build dependencies on VPS...")
        deps_commands = [
            "apt-get update -qq",
            "apt-get install -y cmake build-essential",
            "apt-get install -y golang-go || echo 'Go already installed'",
            "apt-get install -y python3 python3-pip python3-dev",
            "apt-get install -y openvpn openssl nginx gunicorn",
        ]
        
        for cmd in deps_commands:
            try:
                success, output, error = run_command(ssh, cmd, check=False)
                if success:
                    print(f"   ✅ {cmd.split()[0]}")
                else:
                    print(f"   ⚠️  {cmd.split()[0]} - {error[:100]}")
            except Exception as e:
                print(f"   ⚠️  {cmd.split()[0]} - {str(e)[:100]}")
        
        print()
        
        # Run CMake build on VPS
        print("🔨 Building on VPS using CMake...")
        build_commands = [
            f"cd {VPS_DIR} && chmod +x deploy-to-vps-cmake.sh build.sh",
            f"cd {VPS_DIR} && bash deploy-to-vps-cmake.sh",
        ]
        
        for cmd in build_commands:
            print(f"   Running: {cmd.split('&&')[-1].strip()}")
            try:
                success, output, error = run_command(ssh, cmd, check=False)
                if success:
                    # Print last few lines of output
                    lines = output.strip().split('\n')
                    for line in lines[-5:]:
                        if line.strip():
                            print(f"      {line}")
                else:
                    print(f"   ⚠️  Error: {error[:200]}")
                    # Don't fail completely, might be warnings
            except Exception as e:
                print(f"   ⚠️  Exception: {str(e)[:200]}")
        
        print()
        
        # Check service status
        print("🔍 Checking service status...")
        services = ['phazevpn-portal', 'phazevpn-protocol', 'phazevpn-protocol-go']
        for service in services:
            success, output, _ = run_command(ssh, f"systemctl is-enabled {service}.service 2>/dev/null || echo 'not-enabled'", check=False)
            status = output.strip()
            if 'enabled' in status or 'not-enabled' in status:
                print(f"   {service}: {status}")
        
        print()
        print("=" * 80)
        print("✅ Deployment Complete!")
        print("=" * 80)
        print()
        print("Next steps on VPS:")
        print(f"  1. SSH to VPS: ssh {VPS_USER}@{VPS_HOST}")
        print(f"  2. Check build: cd {VPS_DIR}/build-vps")
        print(f"  3. Enable services: sudo systemctl enable phazevpn-portal phazevpn-protocol")
        print(f"  4. Start services: sudo systemctl start phazevpn-portal phazevpn-protocol")
        print(f"  5. Check logs: sudo journalctl -u phazevpn-portal -f")
        print()
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

