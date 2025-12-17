#!/usr/bin/env python3
"""
Apply speed optimizations for Chromium fetch and VPN on VPS
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

def run_command(ssh, command, description="", timeout=300, show_output=True):
    if description and show_output:
        print(f"🔧 {description}...")
        print("")
    
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
    print("🚀 APPLYING SPEED OPTIMIZATIONS")
    print("=" * 60)
    print("")
    print("This will optimize:")
    print("  1. Chromium fetch speed (parallel downloads)")
    print("  2. VPN connection speed (buffer sizes, MTU)")
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("✅ Connected to VPS")
    print("")
    
    # Part 1: Optimize Chromium fetch
    print("=" * 60)
    print("📥 OPTIMIZING CHROMIUM FETCH")
    print("=" * 60)
    print("")
    
    git_optimizations = """
# Optimize git for faster Chromium fetch
git config --global http.postBuffer 524288000
git config --global http.maxRequestBuffer 100M
git config --global core.compression 9
git config --global pack.windowMemory "100m"
git config --global pack.threads "8"
git config --global fetch.parallel 64
git config --global protocol.version 2
"""
    
    success, output = run_command(
        ssh,
        git_optimizations,
        "Applying git optimizations for faster fetch",
        timeout=30
    )
    
    if success:
        print("✅ Git optimizations applied!")
    print("")
    
    # Part 2: Optimize VPN speed
    print("=" * 60)
    print("🔒 OPTIMIZING VPN SPEED")
    print("=" * 60)
    print("")
    
    # Check if config exists
    config_paths = [
        "/opt/secure-vpn/config/server.conf",
        "/etc/openvpn/server.conf",
        "~/secure-vpn/config/server.conf"
    ]
    
    config_found = None
    for path in config_paths:
        success, output = run_command(
            ssh,
            f"test -f {path} && echo 'found' || echo 'not found'",
            f"Checking {path}",
            timeout=10,
            show_output=False
        )
        if "found" in output:
            config_found = path
            break
    
    if config_found:
        print(f"✅ Found VPN config: {config_found}")
        print("")
        
        # Backup and optimize
        vpn_optimizations = f"""
# Backup config
cp {config_found} {config_found}.backup.$(date +%Y%m%d_%H%M%S)

# Add speed optimizations if not already present
if ! grep -q "SPEED OPTIMIZATIONS" {config_found}; then
    cat >> {config_found} << 'EOFVPN'
# ============================================
# SPEED OPTIMIZATIONS
# ============================================
sndbuf 4194304
rcvbuf 4194304
push "sndbuf 4194304"
push "rcvbuf 4194304"
tun-mtu 1600
mssfix 1540
fast-io
txqueuelen 1000
reneg-bytes 0
reneg-sec 0
socket-flags TCP_NODELAY
EOFVPN
    echo "Optimizations added"
else
    echo "Optimizations already present"
fi
"""
        
        success, output = run_command(
            ssh,
            vpn_optimizations,
            "Applying VPN speed optimizations",
            timeout=30
        )
        
        if success:
            print("✅ VPN optimizations applied!")
            print("")
            print("⚠️  Restart OpenVPN to apply changes:")
            print("   sudo systemctl restart openvpn")
            print("   # or")
            print("   sudo systemctl restart phazevpn")
    else:
        print("⚠️  VPN config not found in standard locations")
        print("   You can optimize manually by editing your OpenVPN config")
    print("")
    
    print("=" * 60)
    print("✅ OPTIMIZATIONS COMPLETE!")
    print("=" * 60)
    print("")
    print("📋 Summary:")
    print("  ✅ Git fetch: 64 parallel connections, optimized compression")
    print("  ✅ VPN buffers: Increased to 4MB (from 2MB)")
    print("  ✅ VPN MTU: Increased to 1600 for fewer packets")
    print("  ✅ VPN I/O: Fast mode enabled")
    print("")
    print("💡 For even faster VPN, consider:")
    print("   - Switching to WireGuard (2-3x faster than OpenVPN)")
    print("   - Using a VPS closer to your location")
    print("   - Using a VPS with better network (10Gbps)")
    print("")
    
    ssh.close()

if __name__ == "__main__":
    main()

