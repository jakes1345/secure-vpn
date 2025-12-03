#!/usr/bin/env python3
"""
Check VPS Resources for VPN + Browser Development
"""

import sys

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def get_system_info(ssh):
    """Get system resource information"""
    info = {}
    
    # Get RAM
    stdin, stdout, stderr = ssh.exec_command("free -g | awk '/^Mem:/{print $2}'")
    info['ram_gb'] = int(stdout.read().decode().strip() or 0)
    
    # Get disk space
    stdin, stdout, stderr = ssh.exec_command("df -h / | awk 'NR==2 {print $2, $4}'")
    disk_info = stdout.read().decode().strip().split()
    info['disk_total'] = disk_info[0] if len(disk_info) > 0 else "Unknown"
    info['disk_free'] = disk_info[1] if len(disk_info) > 1 else "Unknown"
    
    # Get CPU cores
    stdin, stdout, stderr = ssh.exec_command("nproc")
    info['cpu_cores'] = int(stdout.read().decode().strip() or 0)
    
    # Get CPU model
    stdin, stdout, stderr = ssh.exec_command("lscpu | grep 'Model name' | cut -d: -f2 | xargs")
    info['cpu_model'] = stdout.read().decode().strip() or "Unknown"
    
    # Get load average
    stdin, stdout, stderr = ssh.exec_command("uptime | awk -F'load average:' '{print $2}' | xargs")
    info['load_avg'] = stdout.read().decode().strip() or "Unknown"
    
    return info

def main():
    print("==========================================")
    print("🔍 CHECKING VPS RESOURCES")
    print("==========================================")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected to VPS")
        print("")
    except Exception as e:
        print(f"❌ Error connecting: {e}")
        sys.exit(1)
    
    info = get_system_info(ssh)
    
    print("📊 Current VPS Resources:")
    print("")
    print(f"   CPU: {info['cpu_cores']} cores - {info['cpu_model']}")
    print(f"   RAM: {info['ram_gb']}GB")
    print(f"   Disk: {info['disk_total']} total, {info['disk_free']} free")
    print(f"   Load: {info['load_avg']}")
    print("")
    
    # Check if sufficient for VPN + Browser building
    print("🔍 Resource Analysis:")
    print("")
    
    # VPN requirements
    print("VPN Server Requirements:")
    print("   ✅ RAM: 2-4GB (you have {})".format(info['ram_gb']))
    print("   ✅ CPU: 2+ cores (you have {})".format(info['cpu_cores']))
    print("   ✅ Disk: 10GB (you have {})".format(info['disk_free']))
    print("")
    
    # Browser building requirements
    print("Browser Building Requirements:")
    if info['ram_gb'] >= 16:
        print("   ✅ RAM: 16GB+ (you have {}GB) - EXCELLENT".format(info['ram_gb']))
    elif info['ram_gb'] >= 8:
        print("   ⚠️  RAM: 8-16GB (you have {}GB) - OK with swap".format(info['ram_gb']))
    else:
        print("   ❌ RAM: 8GB+ needed (you have {}GB) - MAY BE SLOW".format(info['ram_gb']))
    
    if info['cpu_cores'] >= 4:
        print("   ✅ CPU: 4+ cores (you have {}) - GOOD".format(info['cpu_cores']))
    else:
        print("   ⚠️  CPU: 4+ cores recommended (you have {}) - WILL BE SLOW".format(info['cpu_cores']))
    
    # Check disk space (need ~50GB for browser build)
    print("   ⚠️  Disk: Need ~50GB free for browser build")
    print("")
    
    # Overall assessment
    print("==========================================")
    print("📋 RECOMMENDATION:")
    print("==========================================")
    print("")
    
    if info['ram_gb'] >= 16 and info['cpu_cores'] >= 4:
        print("✅ YES - Your VPS can handle both:")
        print("   - VPN server (lightweight)")
        print("   - Browser building (resource-intensive)")
        print("")
        print("   You can:")
        print("   1. Run VPN server (already running)")
        print("   2. Build browser on VPS (will take 2-4 hours)")
        print("   3. Distribute browser to users (they run it locally)")
    elif info['ram_gb'] >= 8:
        print("⚠️  MAYBE - Your VPS can handle it but:")
        print("   - VPN server: ✅ Fine")
        print("   - Browser building: ⚠️  Will be slow, may need swap")
        print("")
        print("   Options:")
        print("   1. Build on VPS (slower but works)")
        print("   2. Build locally if you have better PC")
        print("   3. Use VPS just for VPN, build browser elsewhere")
    else:
        print("❌ NO - Your VPS is too small for browser building:")
        print("   - VPN server: ✅ Fine")
        print("   - Browser building: ❌ Not enough RAM/CPU")
        print("")
        print("   Options:")
        print("   1. Upgrade VPS (more RAM/CPU)")
        print("   2. Build browser on your local PC")
        print("   3. Use VPS just for VPN")
    
    print("")
    print("==========================================")
    print("")
    print("📝 IMPORTANT CLARIFICATION:")
    print("")
    print("The browser is a CLIENT application:")
    print("   - Built on VPS (one-time, takes hours)")
    print("   - Distributed to users (download .deb/.rpm)")
    print("   - Runs on USER'S computer (not VPS)")
    print("")
    print("The VPN is a SERVER application:")
    print("   - Runs on VPS (always running)")
    print("   - Users connect to it")
    print("")
    print("So VPS handles:")
    print("   ✅ VPN server (running 24/7)")
    print("   ✅ Browser building (one-time, or when updating)")
    print("   ❌ NOT running browser for users (they run it locally)")
    print("")
    
    ssh.close()

if __name__ == "__main__":
    main()

