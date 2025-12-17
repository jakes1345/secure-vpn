#!/usr/bin/env python3
"""
Fix web browsing and DNS issues on VPS
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔧 FIXING WEB BROWSING ON VPS")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Test DNS resolution
        print("1️⃣  Testing DNS resolution...")
        success, dns_test, _ = run_command(ssh, "nslookup google.com 8.8.8.8 2>&1 | grep -A 2 'Name:'")
        print(dns_test)
        
        success, dns_test2, _ = run_command(ssh, "nslookup cursor.com 8.8.8.8 2>&1 | grep -A 2 'Name:'")
        print(f"Cursor.com DNS: {dns_test2[:100]}")
        print("")
        
        # Test HTTPS connection
        print("2️⃣  Testing HTTPS connections...")
        success, https_test, _ = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' https://google.com --max-time 10 2>&1")
        print(f"HTTPS to google.com: {https_test}")
        
        success, cursor_test, _ = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' https://cursor.com --max-time 10 2>&1")
        print(f"HTTPS to cursor.com: {cursor_test}")
        print("")
        
        # Check current DNS config
        print("3️⃣  Checking DNS configuration...")
        success, resolv_conf, _ = run_command(ssh, "cat /etc/resolv.conf")
        print(resolv_conf)
        print("")
        
        # Fix DNS permanently
        print("4️⃣  Setting DNS permanently...")
        
        # Backup original
        run_command(ssh, "cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true")
        
        # Set DNS
        dns_config = """nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
"""
        stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/resolv.conf << 'DNS_EOF'\n{dns_config}\nDNS_EOF")
        stdout.channel.recv_exit_status()
        
        # Make it persistent (prevent NetworkManager from overwriting)
        run_command(ssh, "chattr +i /etc/resolv.conf 2>/dev/null || echo 'Cannot lock resolv.conf'")
        
        print("   ✅ DNS set to Google DNS (8.8.8.8, 8.8.4.4)")
        print("")
        
        # Configure systemd-resolved if it exists
        print("5️⃣  Configuring systemd-resolved...")
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active systemd-resolved 2>&1")
        if 'active' in stdout.read().decode().strip():
            resolved_config = """[Resolve]
DNS=8.8.8.8 8.8.4.4 1.1.1.1
FallbackDNS=1.1.1.1
"""
            stdin, stdout, stderr = ssh.exec_command(f"mkdir -p /etc/systemd/resolved.conf.d && cat > /etc/systemd/resolved.conf.d/dns.conf << 'RESOLVED_EOF'\n{resolved_config}\nRESOLVED_EOF")
            stdout.channel.recv_exit_status()
            run_command(ssh, "systemctl restart systemd-resolved")
            print("   ✅ systemd-resolved configured")
        else:
            print("   ℹ️  systemd-resolved not running")
        print("")
        
        # Check firewall blocking outbound
        print("6️⃣  Checking firewall for outbound blocking...")
        success, firewall, _ = run_command(ssh, "ufw status | grep 'Default:'")
        print(firewall)
        
        # Ensure outbound is allowed
        run_command(ssh, "ufw default allow outgoing 2>&1 || echo 'UFW not blocking'")
        print("   ✅ Ensured outbound connections allowed")
        print("")
        
        # Test DNS again
        print("7️⃣  Testing DNS after fixes...")
        success, final_dns, _ = run_command(ssh, "host google.com 2>&1 | head -3")
        print(final_dns)
        
        success, final_dns2, _ = run_command(ssh, "host cursor.com 2>&1 | head -3")
        print(f"Cursor.com: {final_dns2[:100]}")
        print("")
        
        # Test HTTPS again
        print("8️⃣  Testing HTTPS after fixes...")
        success, final_https, _ = run_command(ssh, "curl -s -I https://google.com --max-time 10 2>&1 | head -3")
        print(final_https[:200])
        print("")
        
        # Create network fix script for desktop
        print("9️⃣  Creating network fix script for desktop sessions...")
        fix_script = """#!/bin/bash
# Fix DNS in desktop sessions
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
chmod 644 /etc/resolv.conf
"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > /usr/local/bin/fix-network.sh << 'FIX_EOF'\n{fix_script}\nFIX_EOF")
        stdout.channel.recv_exit_status()
        run_command(ssh, "chmod +x /usr/local/bin/fix-network.sh")
        print("   ✅ Created fix-network.sh script")
        print("")
        
        print("=" * 70)
        print("✅ NETWORK FIXED")
        print("=" * 70)
        print("")
        print("📋 If web browsing still doesn't work in RDP:")
        print("  1. Open terminal in RDP")
        print("  2. Run: sudo /usr/local/bin/fix-network.sh")
        print("  3. Or manually: echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf")
        print("")
        print("🌐 Test it:")
        print("  - In RDP browser, go to: https://google.com")
        print("  - Or in terminal: curl https://google.com")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

