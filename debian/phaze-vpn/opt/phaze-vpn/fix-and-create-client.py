#!/usr/bin/env python3
"""Fix missing files and create a client"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

client_name = sys.argv[1] if len(sys.argv) > 1 else "myclient"

print(f"🔧 Fixing missing files and creating client: {client_name}\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

# Create missing openssl-client.cnf file
print("📝 Creating missing OpenSSL config file...")
openssl_client_cnf = f"""[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
"""

sftp = ssh.open_sftp()
file = sftp.file(f"{VPN_DIR}/certs/openssl-client.cnf", "w")
file.write(openssl_client_cnf)
file.close()
sftp.close()

print("✅ OpenSSL config created\n")

# Now create the client
print(f"📝 Creating client '{client_name}'...")
output, errors, status = run(f"cd {VPN_DIR} && python3 vpn-manager.py add-client {client_name}")

if status == 0:
    print("✅ Client created successfully!\n")
    
    # Check config file
    output, _, _ = run(f"test -f {VPN_DIR}/client-configs/{client_name}.ovpn && echo 'EXISTS' || echo 'MISSING'")
    if "EXISTS" in output:
        print(f"✅ Config file: {VPN_DIR}/client-configs/{client_name}.ovpn")
        
        print("\n" + "="*60)
        print("✅ Client Ready!")
        print("="*60)
        print(f"\n📱 Download URL:")
        print(f"   http://{VPS_IP}:8081/download?name={client_name}")
        print(f"\n📁 Or via SSH:")
        print(f"   scp {VPS_USER}@{VPS_IP}:{VPN_DIR}/client-configs/{client_name}.ovpn .")
        print("\n✅ Works on all platforms (Windows, Linux, macOS, iPhone, Android)")
        print("="*60)
    else:
        print("⚠️  Config may have been created but file check failed")
else:
    print(f"❌ Failed: {errors}")
    print(output)

ssh.close()

