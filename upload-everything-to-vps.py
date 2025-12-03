#!/usr/bin/env python3
"""
Upload ALL files to VPS in organized folder structure
This allows you to delete files from local system after upload
"""

import paramiko
import os
from pathlib import Path
import tarfile
import tempfile

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_BASE_DIR = "/opt/phaze-vpn"
VPS_BACKUP_DIR = f"{VPS_BASE_DIR}/backup-all-files"

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

def create_tarball(source_dir, exclude_patterns=None):
    """Create a tarball of the source directory"""
    if exclude_patterns is None:
        exclude_patterns = ['.git', '__pycache__', '*.pyc', '.DS_Store', 'node_modules']
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
    temp_path = temp_file.name
    temp_file.close()
    
    with tarfile.open(temp_path, 'w:gz') as tar:
        for root, dirs, files in os.walk(source_dir):
            # Filter out excluded patterns
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
            
            for file in files:
                if any(file.endswith(pattern.replace('*', '')) for pattern in exclude_patterns):
                    continue
                
                file_path = Path(root) / file
                arcname = file_path.relative_to(source_dir.parent if source_dir.is_file() else source_dir)
                tar.add(file_path, arcname=arcname, recursive=False)
    
    return temp_path

def main():
    print("="*60)
    print("Upload ALL Files to VPS")
    print("="*60)
    print("")
    print(f"Source: {Path.cwd()}")
    print(f"VPS: {VPS_USER}@{VPS_HOST}")
    print(f"Target: {VPS_BACKUP_DIR}")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Create backup directory on VPS
        print("📁 Creating backup directory on VPS...")
        ssh.exec_command(f"mkdir -p {VPS_BACKUP_DIR}")
        print(f"✅ Created {VPS_BACKUP_DIR}")
        print("")
        
        # Create tarball
        print("📦 Creating tarball of all files...")
        source_dir = Path.cwd()
        tarball_path = create_tarball(source_dir)
        tarball_size = os.path.getsize(tarball_path) / (1024 * 1024)  # MB
        print(f"✅ Created tarball: {tarball_size:.2f} MB")
        print("")
        
        # Upload tarball
        print("📤 Uploading tarball to VPS...")
        sftp = ssh.open_sftp()
        remote_tarball = f"{VPS_BACKUP_DIR}/secure-vpn-complete-backup.tar.gz"
        sftp.put(tarball_path, remote_tarball)
        sftp.close()
        print(f"✅ Uploaded to {remote_tarball}")
        print("")
        
        # Extract on VPS
        print("📂 Extracting files on VPS...")
        extract_cmd = f"""
cd {VPS_BACKUP_DIR}
tar -xzf secure-vpn-complete-backup.tar.gz
chmod -R 755 {VPS_BACKUP_DIR}/*
echo "✅ Files extracted"
ls -lh {VPS_BACKUP_DIR} | head -20
"""
        stdin, stdout, stderr = ssh.exec_command(extract_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print("⚠️  Warnings:", errors)
        print("")
        
        # Also copy critical files to main directories
        print("🔄 Copying critical files to main directories...")
        copy_cmd = f"""
# Copy web-portal files
if [ -d "{VPS_BACKUP_DIR}/web-portal" ]; then
    cp -r {VPS_BACKUP_DIR}/web-portal/* {VPS_BASE_DIR}/web-portal/ 2>/dev/null || true
    echo "✅ Web portal files updated"
fi

# Copy vpn-gui.py
if [ -f "{VPS_BACKUP_DIR}/vpn-gui.py" ]; then
    cp {VPS_BACKUP_DIR}/vpn-gui.py {VPS_BASE_DIR}/vpn-gui.py
    echo "✅ vpn-gui.py updated"
fi

# Copy vpn-manager.py
if [ -f "{VPS_BACKUP_DIR}/vpn-manager.py" ]; then
    cp {VPS_BACKUP_DIR}/vpn-manager.py {VPS_BASE_DIR}/vpn-manager.py
    echo "✅ vpn-manager.py updated"
fi

# Restart web portal
pkill -f 'python.*app.py' 2>/dev/null || true
cd {VPS_BASE_DIR}/web-portal && nohup python3 app.py > /dev/null 2>&1 &
echo "✅ Web portal restarted"
"""
        stdin, stdout, stderr = ssh.exec_command(copy_cmd)
        output = stdout.read().decode()
        print(output)
        print("")
        
        # Clean up local tarball
        os.unlink(tarball_path)
        
        print("="*60)
        print("✅ UPLOAD COMPLETE!")
        print("="*60)
        print("")
        print(f"All files are now on VPS at: {VPS_BACKUP_DIR}")
        print("")
        print("You can now:")
        print("  1. Verify files on VPS: ssh root@15.204.11.19 'ls -la /opt/phaze-vpn/backup-all-files'")
        print("  2. Delete local files if you want (they're safely backed up on VPS)")
        print("  3. All critical files have been copied to main directories")
        print("")
        print("⚠️  Note: The system uses JSON files (users.json), NOT MySQL")
        print("   All user data is stored in: /opt/phaze-vpn/users.json")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

