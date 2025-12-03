#!/usr/bin/env python3
"""
Fix OpenVPN service - Set up proper paths for systemd
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔧 FIXING OPENVPN SERVICE")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Step 1: Stop everything
    print("1️⃣ Stopping all OpenVPN processes...")
    ssh.exec_command("pkill -f openvpn; systemctl stop openvpn@server; sleep 2")
    print("   ✅ Stopped")
    print("")
    
    # Step 2: Check where certs are
    print("2️⃣ Checking certificate locations...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /opt/secure-vpn/certs/ 2>&1 | head -10")
    certs = stdout.read().decode()
    print(certs)
    
    if "No such file" in certs:
        print("   ⚠️  Certs directory not found!")
        stdin, stdout, stderr = ssh.exec_command("find /opt/secure-vpn -name '*.crt' -o -name '*.key' -o -name '*.pem' | head -5")
        found = stdout.read().decode()
        print(f"   Found: {found}")
    print("")
    
    # Step 3: Create /etc/openvpn structure
    print("3️⃣ Setting up /etc/openvpn...")
    ssh.exec_command("mkdir -p /etc/openvpn/certs")
    print("   ✅ Created directories")
    print("")
    
    # Step 4: Copy config and certs
    print("4️⃣ Copying config and certificates...")
    
    # Copy config
    ssh.exec_command("cp /opt/secure-vpn/config/server.conf /etc/openvpn/server.conf")
    
    # Copy certs if they exist
    stdin, stdout, stderr = ssh.exec_command("test -d /opt/secure-vpn/certs && echo 'exists' || echo 'missing'")
    if "exists" in stdout.read().decode():
        ssh.exec_command("cp -r /opt/secure-vpn/certs/* /etc/openvpn/certs/ 2>&1")
        print("   ✅ Copied certificates")
    else:
        # Check if certs are in a different location
        stdin, stdout, stderr = ssh.exec_command("find /opt/secure-vpn -type d -name 'certs' | head -1")
        cert_dir = stdout.read().decode().strip()
        if cert_dir:
            ssh.exec_command(f"cp -r {cert_dir}/* /etc/openvpn/certs/ 2>&1")
            print(f"   ✅ Copied certificates from {cert_dir}")
        else:
            print("   ⚠️  No certificates found - may need to generate them")
    
    print("   ✅ Config copied")
    print("")
    
    # Step 5: Verify files
    print("5️⃣ Verifying files...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /etc/openvpn/server.conf && echo '---' && ls -la /etc/openvpn/certs/ | head -10")
    files = stdout.read().decode()
    print(files)
    print("")
    
    # Step 6: Start service
    print("6️⃣ Starting OpenVPN service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl start openvpn@server && sleep 3 && systemctl status openvpn@server --no-pager | head -15")
    status = stdout.read().decode()
    print(status)
    
    if "active (running)" in status:
        print("   ✅ OpenVPN is running!")
    else:
        print("   ⚠️  Service may still be starting...")
        stdin, stdout, stderr = ssh.exec_command("journalctl -u openvpn@server -n 10 --no-pager")
        logs = stdout.read().decode()
        print("   Recent logs:")
        print(logs)
    print("")
    
    # Step 7: Final check
    print("7️⃣ Final status check...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active openvpn@server && echo '---' && pgrep -a openvpn && echo '---' && ss -ulnp | grep 1194")
    final = stdout.read().decode()
    print(final)
    print("")
    
    print("=" * 60)
    print("✅ FIX COMPLETE")
    print("=" * 60)
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

