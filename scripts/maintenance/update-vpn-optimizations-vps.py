#!/usr/bin/env python3
"""
Update VPN config with latest optimizations and restart
"""

import sys
import re

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description="", timeout=300):
    if description:
        print(f"🔧 {description}...")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        output_lines = []
        for line in iter(stdout.readline, ""):
            if line:
                output_lines.append(line.rstrip())
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, "\n".join(output_lines)
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("🚀 UPDATING VPN OPTIMIZATIONS")
    print("=" * 60)
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    config_file = "/opt/secure-vpn/config/server.conf"
    
    # Read current config
    success, config_content = run_command(
        ssh,
        f"cat {config_file}",
        "Reading current config",
        timeout=30
    )
    
    if not success:
        print("❌ Could not read config file")
        ssh.close()
        return
    
    # Update buffers from 2MB to 4MB
    updated = config_content
    updated = re.sub(r'sndbuf\s+2097152', 'sndbuf 4194304', updated)
    updated = re.sub(r'rcvbuf\s+2097152', 'rcvbuf 4194304', updated)
    updated = re.sub(r'"sndbuf 2097152"', '"sndbuf 4194304"', updated)
    updated = re.sub(r'"rcvbuf 2097152"', '"rcvbuf 4194304"', updated)
    
    # Update MTU from 1500 to 1600
    updated = re.sub(r'tun-mtu\s+1500', 'tun-mtu 1600', updated)
    updated = re.sub(r'mssfix\s+1450', 'mssfix 1540', updated)
    
    # Add fast-io if not present
    if 'fast-io' not in updated:
        # Find Performance Optimization section
        if '# Performance Optimization' in updated:
            updated = updated.replace(
                '# Performance Optimization',
                '# Performance Optimization\nfast-io'
            )
        else:
            # Add at end
            updated += '\nfast-io\n'
    
    # Write updated config
    import base64
    config_b64 = base64.b64encode(updated.encode()).decode()
    
    success, output = run_command(
        ssh,
        f"""python3 -c "import base64; f=open('{config_file}', 'w'); f.write(base64.b64decode('{config_b64}').decode()); f.close()" """,
        "Writing updated config",
        timeout=30
    )
    
    if success:
        print("✅ Config updated!")
        print("")
        print("📋 Changes:")
        print("   ✅ Buffers: 2MB → 4MB")
        print("   ✅ MTU: 1500 → 1600")
        print("   ✅ Fast I/O: Enabled")
        print("")
        
        # Restart OpenVPN
        print("🔄 Restarting OpenVPN...")
        run_command(
            ssh,
            "systemctl restart openvpn@server 2>&1 || systemctl restart phazevpn 2>&1",
            "Restarting OpenVPN",
            timeout=30
        )
        
        print("")
        print("✅ VPN optimizations applied and restarted!")
    else:
        print("⚠️  Could not update config, but continuing...")
    
    ssh.close()

if __name__ == "__main__":
    main()

