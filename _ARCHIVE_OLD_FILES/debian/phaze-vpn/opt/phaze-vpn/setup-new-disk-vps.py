#!/usr/bin/env python3
"""
Setup the new 100GB disk (sdb) on VPS
Either mount it separately or use it for Chromium build
"""

import sys

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed. Install with: pip install paramiko")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description="", timeout=300, show_output=True):
    """Run a command and return output"""
    if description and show_output:
        print(f"🔧 {description}...")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        
        output_lines = []
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                if show_output:
                    print(f"   {line}")
                output_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, "\n".join(output_lines)
            
    except Exception as e:
        if show_output:
            print(f"   ❌ Error: {e}")
        return False, str(e)

def main():
    print("=" * 60)
    print("💾 SETTING UP NEW 100GB DISK")
    print("=" * 60)
    print("")
    
    # Connect
    print("🔌 Connecting to VPS...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    print("")
    
    try:
        # Check sdb status
        print("=" * 60)
        print("📊 CHECKING NEW DISK (sdb)")
        print("=" * 60)
        print("")
        
        success, output = run_command(ssh, "lsblk /dev/sdb", "Checking sdb disk", timeout=10)
        
        print("")
        
        # Check if it has a filesystem
        success, output = run_command(ssh, "blkid /dev/sdb 2>/dev/null || echo 'No filesystem'", "Checking for filesystem", timeout=10)
        
        print("")
        
        # Check if it's mounted
        success, output = run_command(ssh, "mount | grep sdb || echo 'Not mounted'", "Checking if mounted", timeout=10)
        
        print("")
        print("=" * 60)
        print("🔧 SETTING UP NEW DISK")
        print("=" * 60)
        print("")
        
        # Check if sdb has partitions
        success, output = run_command(ssh, "lsblk /dev/sdb | grep -E 'sdb[0-9]' || echo 'No partitions'", "Checking for partitions", timeout=10, show_output=False)
        
        if "No partitions" in output:
            print("📝 Creating partition on sdb...")
            print("")
            
            # Create partition table and partition
            print("   Creating partition table...")
            success, output = run_command(ssh, "parted /dev/sdb --script mklabel gpt", "Creating GPT partition table", timeout=30)
            
            if success:
                print("   ✅ Partition table created")
                print("")
                print("   Creating partition (using full disk)...")
                success, output = run_command(ssh, "parted /dev/sdb --script mkpart primary ext4 0% 100%", "Creating partition", timeout=30)
                
                if success:
                    print("   ✅ Partition created")
                    print("")
                    print("   Formatting as ext4...")
                    success, output = run_command(ssh, "mkfs.ext4 -F /dev/sdb1", "Formatting filesystem", timeout=120)
                    
                    if success:
                        print("   ✅ Filesystem created")
                        print("")
                    else:
                        print("   ❌ Failed to format")
                        ssh.close()
                        return
                else:
                    print("   ❌ Failed to create partition")
                    ssh.close()
                    return
            else:
                print("   ❌ Failed to create partition table")
                ssh.close()
                return
        else:
            print("   Partition already exists, checking filesystem...")
            success, output = run_command(ssh, "blkid /dev/sdb1 2>/dev/null || blkid /dev/sdb", "Checking filesystem", timeout=10, show_output=False)
            
            if "ext4" not in output and "ext3" not in output:
                print("   Formatting as ext4...")
                device = "/dev/sdb1" if "sdb1" in output else "/dev/sdb"
                success, output = run_command(ssh, f"mkfs.ext4 -F {device}", "Formatting filesystem", timeout=120)
                
                if success:
                    print("   ✅ Filesystem created")
                else:
                    print("   ⚠️  Formatting had issues")
        
        print("")
        print("=" * 60)
        print("📁 MOUNTING NEW DISK")
        print("=" * 60)
        print("")
        
        # Create mount point
        mount_point = "/mnt/extra-disk"
        print(f"   Creating mount point: {mount_point}")
        run_command(ssh, f"mkdir -p {mount_point}", "Creating mount point", timeout=10)
        
        # Find the device
        success, output = run_command(ssh, "lsblk -o NAME,TYPE /dev/sdb | grep part | awk '{print \"/dev/\"$1}' || echo '/dev/sdb1'", "Finding partition device", timeout=10, show_output=False)
        device = output.strip() if success and output.strip() else "/dev/sdb1"
        
        print(f"   Mounting {device} to {mount_point}...")
        success, output = run_command(ssh, f"mount {device} {mount_point}", "Mounting disk", timeout=30)
        
        if success:
            print("   ✅ Disk mounted!")
            print("")
            
            # Add to fstab for persistence
            print("   Adding to /etc/fstab for auto-mount...")
            success, output = run_command(ssh, f"grep -q '{mount_point}' /etc/fstab || echo '{device} {mount_point} ext4 defaults 0 2' >> /etc/fstab", "Adding to fstab", timeout=10)
            
            if success:
                print("   ✅ Added to fstab")
            
            print("")
            print("=" * 60)
            print("✅ NEW DISK SETUP COMPLETE!")
            print("=" * 60)
            print("")
            
            # Show disk usage
            success, output = run_command(ssh, f"df -h {mount_point}", "New disk usage", timeout=10)
            
            print("")
            print("💡 OPTIONS FOR USING THE NEW DISK:")
            print("")
            print("Option 1: Move Chromium build to new disk")
            print(f"   mkdir -p {mount_point}/phazebrowser")
            print(f"   mv /opt/phazebrowser/src {mount_point}/phazebrowser/")
            print(f"   ln -s {mount_point}/phazebrowser/src /opt/phazebrowser/src")
            print("")
            print("Option 2: Use new disk for build output only")
            print(f"   mkdir -p {mount_point}/chromium-build")
            print("   # Then build to: {mount_point}/chromium-build")
            print("")
            print("Option 3: Keep using main disk (if you expand sda1 instead)")
            print("")
            
        else:
            print("   ❌ Failed to mount disk")
            print("   Check logs above for errors")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

