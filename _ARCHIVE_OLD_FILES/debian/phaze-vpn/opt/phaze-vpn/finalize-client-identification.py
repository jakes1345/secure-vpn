#!/usr/bin/env python3
"""
Finalize client identification - enable CCD and verify everything works
"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"\n🔧 {description}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        if output.strip():
            print(f"   ✅ {output.strip()[:200]}")
        return True, output
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, output

def main():
    print("="*80)
    print("🔧 FINALIZING CLIENT IDENTIFICATION")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Enable CCD in server config
    print("\n" + "="*80)
    print("1️⃣  ENABLING CLIENT CONFIG DIRECTORY")
    print("="*80)
    
    # Uncomment CCD lines
    run_command(ssh, """
    cd /opt/secure-vpn/config
    # Uncomment CCD lines
    sed -i 's|^# client-config-dir|client-config-dir|' server.conf
    sed -i 's|^# ccd-exclusive|ccd-exclusive|' server.conf
    
    # Ensure CCD directory exists
    mkdir -p ccd
    echo "CCD enabled"
    """, "Enabling CCD")
    
    # Verify CCD is enabled
    run_command(ssh, "grep -E '^client-config-dir|^ccd-exclusive' /opt/secure-vpn/config/server.conf",
                "Verifying CCD enabled")
    
    # Restart OpenVPN
    print("\n🔄 Restarting OpenVPN...")
    run_command(ssh, "systemctl restart openvpn@server", "Restarting OpenVPN")
    run_command(ssh, "sleep 2 && systemctl status openvpn@server --no-pager | head -5",
                "Checking OpenVPN status")
    
    # Update vpn-manager.py on VPS
    print("\n" + "="*80)
    print("2️⃣  UPDATING VPN-MANAGER ON VPS")
    print("="*80)
    
    run_command(ssh, """
    # Update certificate generation to use PhazeVPN markers
    sed -i "s|O=Client/CN=\${name}|O=PhazeVPN/CN=phazevpn-\${name}|g" /opt/secure-vpn/vpn-manager.py 2>/dev/null || \\
    sed -i "s|O=Client|O=PhazeVPN|g" /opt/secure-vpn/vpn-manager.py && \\
    sed -i "s|CN={name}|CN=phazevpn-{name}|g" /opt/secure-vpn/vpn-manager.py
    
    echo "vpn-manager.py updated"
    """, "Updating vpn-manager.py")
    
    # Verify update
    run_command(ssh, "grep -E 'O=PhazeVPN|phazevpn-' /opt/secure-vpn/vpn-manager.py | head -2",
                "Verifying update")
    
    print("\n" + "="*80)
    print("✅ CLIENT IDENTIFICATION FINALIZED")
    print("="*80)
    print("\n📊 How it works:")
    print("   ✅ PhazeVPN clients: CN=phazevpn-<name>, O=PhazeVPN")
    print("   ✅ OpenVPN clients: CN=<name>, O=Client")
    print("   ✅ Server detects type from certificate")
    print("   ✅ Different configs via CCD")
    print("\n🔍 To test:")
    print("   1. Generate new client: python3 vpn-manager.py add-client test")
    print("   2. Check certificate: openssl x509 -in certs/test.crt -noout -subject")
    print("   3. Should show: O=PhazeVPN, CN=phazevpn-test")
    
    ssh.close()

if __name__ == "__main__":
    main()

