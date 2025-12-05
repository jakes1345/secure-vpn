#!/usr/bin/env python3
"""
Check VPN performance and status on OVH VPS
"""
import paramiko
import sys
from time import sleep

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run a command via SSH and return output"""
    try:
        if description:
            print(f"\n📊 {description}...")
        stdin, stdout, stderr = ssh.exec_command(command, timeout=15)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output.strip():
            print(output)
        if error.strip() and "warning" not in error.lower():
            print(f"⚠️  Error: {error}", file=sys.stderr)
        
        return output, error
    except Exception as e:
        print(f"❌ Error running command: {e}", file=sys.stderr)
        return "", str(e)

def main():
    print("=" * 70)
    print("🔍 CHECKING VPN PERFORMANCE ON OVH VPS")
    print("=" * 70)
    print(f"\n📡 Connecting to {VPS_USER}@{VPS_HOST}...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected!\n")
        
        # 1. Check system specs
        print("=" * 70)
        print("💻 SYSTEM SPECIFICATIONS")
        print("=" * 70)
        run_command(ssh, "lscpu | grep -E '(Model name|CPU\\(s\\)|Thread|Core|MHz)'", "CPU Info")
        run_command(ssh, "free -h", "Memory")
        run_command(ssh, "df -h / | tail -1", "Disk Space")
        run_command(ssh, "uptime", "System Uptime")
        
        # 2. Check what VPN services are running
        print("\n" + "=" * 70)
        print("🔐 VPN SERVICES STATUS")
        print("=" * 70)
        run_command(ssh, "systemctl list-units --type=service --state=running | grep -iE '(vpn|openvpn|phazevpn)' || echo 'No VPN services found'", "Running VPN Services")
        run_command(ssh, "systemctl list-units --type=service --all | grep -iE '(vpn|openvpn|phazevpn)' | head -10", "All VPN Services")
        
        # 3. Check OpenVPN specifically
        print("\n" + "=" * 70)
        print("🔒 OPENVPN STATUS")
        print("=" * 70)
        run_command(ssh, "systemctl status openvpn@server 2>&1 | head -20 || systemctl status openvpn 2>&1 | head -20 || echo 'OpenVPN service not found'", "OpenVPN Service")
        run_command(ssh, "pgrep -a openvpn || echo 'No OpenVPN process running'", "OpenVPN Processes")
        run_command(ssh, "netstat -tulpn | grep :1194 || ss -tulpn | grep :1194 || echo 'Port 1194 not listening'", "Port 1194 Status")
        
        # 4. Check PhazeVPN Protocol if exists
        print("\n" + "=" * 70)
        print("🚀 PHAZEVPN PROTOCOL STATUS")
        print("=" * 70)
        run_command(ssh, "systemctl status phazevpn-protocol 2>&1 | head -20 || echo 'PhazeVPN Protocol service not found'", "PhazeVPN Protocol Service")
        run_command(ssh, "netstat -tulpn | grep :51821 || ss -tulpn | grep :51821 || echo 'Port 51821 not listening'", "Port 51821 Status")
        
        # 5. Check active connections
        print("\n" + "=" * 70)
        print("👥 ACTIVE VPN CONNECTIONS")
        print("=" * 70)
        run_command(ssh, "ip addr show tun0 2>/dev/null || ip addr show phazevpn0 2>/dev/null || echo 'No VPN interface found'", "VPN Interface")
        run_command(ssh, "cat /var/log/openvpn/status.log 2>/dev/null | tail -30 || cat /opt/secure-vpn/logs/status.log 2>/dev/null | tail -30 || echo 'No status log found'", "OpenVPN Status Log")
        
        # 6. Network performance
        print("\n" + "=" * 70)
        print("⚡ NETWORK PERFORMANCE")
        print("=" * 70)
        run_command(ssh, "cat /proc/sys/net/core/rmem_max", "Max Receive Buffer")
        run_command(ssh, "cat /proc/sys/net/core/wmem_max", "Max Send Buffer")
        run_command(ssh, "ethtool $(ip route | grep default | awk '{print $5}' | head -1) 2>/dev/null | grep -E '(Speed|Duplex)' || echo 'Cannot get network speed'", "Network Interface Speed")
        
        # 7. CPU and memory usage
        print("\n" + "=" * 70)
        print("📈 RESOURCE USAGE")
        print("=" * 70)
        run_command(ssh, "top -bn1 | head -20", "Current Resource Usage")
        run_command(ssh, "ps aux | grep -E '(openvpn|phazevpn)' | grep -v grep || echo 'No VPN processes found'", "VPN Process Details")
        
        # 8. Check VPN config
        print("\n" + "=" * 70)
        print("⚙️  VPN CONFIGURATION")
        print("=" * 70)
        run_command(ssh, "find /etc/openvpn /opt/secure-vpn -name '*.conf' 2>/dev/null | head -5", "Config Files")
        run_command(ssh, "cat /etc/openvpn/server.conf 2>/dev/null | grep -E '(cipher|auth|proto|port|server)' | head -10 || cat /opt/secure-vpn/config/server.conf 2>/dev/null | grep -E '(cipher|auth|proto|port|server)' | head -10 || echo 'Config file not found'", "VPN Settings")
        
        # 9. Check firewall rules
        print("\n" + "=" * 70)
        print("🔥 FIREWALL RULES")
        print("=" * 70)
        run_command(ssh, "iptables -L -n | grep -E '(1194|51821|ACCEPT|REJECT)' | head -10 || echo 'No relevant firewall rules found'", "Firewall Rules")
        run_command(ssh, "ufw status 2>/dev/null || echo 'UFW not active'", "UFW Status")
        
        # 10. Network latency test (if possible)
        print("\n" + "=" * 70)
        print("🌐 NETWORK LATENCY")
        print("=" * 70)
        run_command(ssh, "ping -c 3 8.8.8.8 2>/dev/null || echo 'Ping test failed'", "Internet Connectivity")
        run_command(ssh, "curl -s -o /dev/null -w 'Download speed test: %{speed_download} bytes/sec\\n' http://speedtest.tele2.net/10MB.zip 2>/dev/null || echo 'Speed test failed'", "Download Speed Test")
        
        print("\n" + "=" * 70)
        print("✅ CHECK COMPLETE!")
        print("=" * 70)
        print("\n📋 Summary:")
        print("   - Checked system specs (CPU, RAM, disk)")
        print("   - Verified VPN services status")
        print("   - Checked active connections")
        print("   - Monitored resource usage")
        print("   - Tested network performance")
        
        ssh.close()
        
    except paramiko.AuthenticationException:
        print("❌ Authentication failed. Please check credentials.")
        print(f"   Trying: {VPS_USER}@{VPS_HOST}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
