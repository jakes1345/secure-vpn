#!/usr/bin/env python3
"""Create a VPN client config quickly"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

if len(sys.argv) < 2:
    print("Usage: python3 create-client.py <client-name>")
    print("\nExample:")
    print("  python3 create-client.py mylaptop")
    print("  python3 create-client.py myphone")
    sys.exit(1)

client_name = sys.argv[1]

print(f"🔐 Creating VPN client: {client_name}\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

# Create the client
print(f"📝 Generating certificate and config for '{client_name}'...")
output, errors, status = run(f"cd {VPN_DIR} && python3 vpn-manager.py add-client {client_name}")

if status == 0:
    print("✅ Client created successfully!\n")
    
    # Check if config file exists
    output, _, _ = run(f"test -f {VPN_DIR}/client-configs/{client_name}.ovpn && echo 'EXISTS' || echo 'MISSING'")
    if "EXISTS" in output:
        print(f"✅ Config file created: {VPN_DIR}/client-configs/{client_name}.ovpn")
        
        print("\n" + "="*60)
        print("✅ Client Ready!")
        print("="*60)
        print(f"\n📱 Download config:")
        print(f"   http://{VPS_IP}:8081/download?name={client_name}")
        print(f"\n📁 Or get it via SSH:")
        print(f"   scp {VPS_USER}@{VPS_IP}:{VPN_DIR}/client-configs/{client_name}.ovpn .")
        print(f"\n📝 Config location on server:")
        print(f"   {VPN_DIR}/client-configs/{client_name}.ovpn")
        print("\n✅ This .ovpn file works on:")
        print("   • Windows (OpenVPN GUI)")
        print("   • Linux (NetworkManager)")
        print("   • macOS (Tunnelblick)")
        print("   • iPhone/iPad (OpenVPN Connect app)")
        print("   • Android (OpenVPN Connect app)")
        print("="*60)
    else:
        print("⚠️  Config file not found, but client may have been created")
        print(output)
else:
    print(f"❌ Failed to create client")
    print(f"Error: {errors}")
    print(f"Output: {output}")
    sys.exit(1)

ssh.close()

