#!/usr/bin/env python3
"""
Expand VPS disk to use newly purchased space
"""

import sys
import time

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
    print("💾 EXPANDING VPS DISK SPACE")
    print("=" * 60)
    print("")
    print("Checking disk and expanding partition to use new space...")
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
        # Check current disk status
        print("=" * 60)
        print("📊 CHECKING CURRENT DISK STATUS")
        print("=" * 60)
        print("")
        
        # Check disk size
        success, output = run_command(ssh, "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT", "Checking disk layout", timeout=30)
        
        print("")
        
        # Check filesystem size
        success, output = run_command(ssh, "df -h /", "Checking filesystem usage", timeout=10)
        
        print("")
        
        # Check if we can see the actual disk size
        success, output = run_command(ssh, "fdisk -l /dev/sda 2>/dev/null | grep 'Disk /dev/sda' || fdisk -l /dev/vda 2>/dev/null | grep 'Disk /dev/vda' || echo 'Could not detect disk'", "Checking actual disk size", timeout=10)
        
        print("")
        print("=" * 60)
        print("🔧 EXPANDING DISK")
        print("=" * 60)
        print("")
        
        # Find the root device
        success, output = run_command(ssh, "df / | tail -1 | awk '{print $1}'", "Finding root device", timeout=10, show_output=False)
        root_device = output.strip() if success else None
        
        if root_device:
            print(f"   Root device: {root_device}")
            
            # Get the physical device (remove partition number)
            if root_device.startswith('/dev/'):
                if 'sda' in root_device:
                    physical_device = '/dev/sda'
                elif 'vda' in root_device:
                    physical_device = '/dev/vda'
                elif 'nvme' in root_device:
                    physical_device = root_device.rsplit('p', 1)[0] if 'p' in root_device else root_device
                else:
                    physical_device = root_device.rstrip('0123456789')
            else:
                physical_device = None
            
            if physical_device:
                print(f"   Physical device: {physical_device}")
                print("")
                
                # Check if we need to resize partition
                print("📝 Attempting to resize partition...")
                print("")
                
                # Try to grow partition (for ext4)
                success, output = run_command(ssh, "growpart --help 2>/dev/null || echo 'growpart not installed'", "Checking for growpart", timeout=10, show_output=False)
                
                if "not installed" not in output:
                    # Use growpart
                    if 'sda' in physical_device or 'vda' in physical_device:
                        partition_num = root_device[-1] if root_device[-1].isdigit() else '1'
                        partition_device = physical_device + partition_num
                        print(f"   Expanding partition {partition_device}...")
                        success, output = run_command(ssh, f"growpart {physical_device} {partition_num}", "Expanding partition", timeout=60)
                        
                        if success:
                            print("   ✅ Partition expanded!")
                            print("")
                            print("   Resizing filesystem...")
                            success2, output2 = run_command(ssh, f"resize2fs {root_device}", "Resizing filesystem", timeout=300)
                            
                            if success2:
                                print("   ✅ Filesystem resized!")
                            else:
                                print("   ⚠️  Filesystem resize had issues")
                        else:
                            print("   ⚠️  Partition expansion had issues")
                            print("   May need manual intervention")
                else:
                    # Install cloud-guest-utils if available
                    print("   Installing growpart...")
                    run_command(ssh, "apt-get update -qq && apt-get install -y cloud-guest-utils 2>&1 | tail -5", "Installing cloud-guest-utils", timeout=120)
                    
                    # Try again
                    if 'sda' in physical_device or 'vda' in physical_device:
                        partition_num = root_device[-1] if root_device[-1].isdigit() else '1'
                        partition_device = physical_device + partition_num
                        print(f"   Expanding partition {partition_device}...")
                        success, output = run_command(ssh, f"growpart {physical_device} {partition_num}", "Expanding partition", timeout=60)
                        
                        if success:
                            print("   ✅ Partition expanded!")
                            print("")
                            print("   Resizing filesystem...")
                            success2, output2 = run_command(ssh, f"resize2fs {root_device}", "Resizing filesystem", timeout=300)
                            
                            if success2:
                                print("   ✅ Filesystem resized!")
                            else:
                                print("   ⚠️  Filesystem resize had issues")
                        else:
                            print("   ⚠️  Could not expand partition automatically")
                            print("   May need to use VPS provider's console/resize tool")
        
        print("")
        print("=" * 60)
        print("📊 CHECKING FINAL DISK STATUS")
        print("=" * 60)
        print("")
        
        success, output = run_command(ssh, "df -h /", "Final disk usage", timeout=10)
        
        print("")
        
        # Check available space
        success, output = run_command(ssh, "df -h / | tail -1 | awk '{print $4}'", "Available space", timeout=10, show_output=False)
        if success:
            avail = output.strip()
            print(f"✅ Available space: {avail}")
            print("")
            
            # Check if we have enough now
            try:
                if 'G' in avail:
                    avail_gb = float(avail.replace('G', ''))
                    if avail_gb >= 20:
                        print("✅ Sufficient space for Chromium build!")
                    else:
                        print("⚠️  Still may not have enough space")
                elif 'T' in avail:
                    print("✅ Plenty of space available!")
                else:
                    print("⚠️  Check space manually")
            except:
                pass
        
        print("")
        print("=" * 60)
        print("✅ DISK EXPANSION COMPLETE!")
        print("=" * 60)
        print("")
        print("💡 If disk wasn't expanded automatically:")
        print("   1. Check your VPS provider's control panel")
        print("   2. Look for 'Resize Disk' or 'Expand Volume' option")
        print("   3. Some providers require a reboot after expansion")
        print("")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

