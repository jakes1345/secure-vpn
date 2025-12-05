#!/usr/bin/env python3
"""
Install and configure WireGuard properly
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔧 INSTALLING AND CONFIGURING WIREGUARD")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Install WireGuard
    print("1️⃣ Installing WireGuard...")
    stdin, stdout, stderr = ssh.exec_command("apt-get update && apt-get install -y wireguard wireguard-tools qrencode")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("   ✅ WireGuard installed")
    else:
        error = stderr.read().decode()
        print(f"   ⚠️  Error: {error[:200]}")
    print("")
    
    # Generate keys
    print("2️⃣ Generating WireGuard keys...")
    stdin, stdout, stderr = ssh.exec_command("wg genkey")
    private_key = stdout.read().decode().strip()
    
    stdin, stdout, stderr = ssh.exec_command(f"echo '{private_key}' | wg pubkey")
    public_key = stdout.read().decode().strip()
    
    print(f"   ✅ Keys generated")
    print(f"   Public Key: {public_key}")
    print("")
    
    # Create config
    print("3️⃣ Creating WireGuard configuration...")
    config = f"""[Interface]
Address = 10.7.0.1/24
ListenPort = 51820
PrivateKey = {private_key}

# Enable NAT
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
"""
    
    sftp = ssh.open_sftp()
    with sftp.file('/etc/wireguard/wg0.conf', 'w') as f:
        f.write(config)
    sftp.close()
    
    # Set permissions
    ssh.exec_command("chmod 600 /etc/wireguard/wg0.conf")
    print("   ✅ Configuration created")
    print("")
    
    # Enable and start
    print("4️⃣ Starting WireGuard...")
    ssh.exec_command("systemctl enable wg-quick@wg0")
    ssh.exec_command("systemctl start wg-quick@wg0")
    time.sleep(2)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active wg-quick@wg0")
    status = stdout.read().decode().strip()
    
    if status == "active":
        print("   ✅ WireGuard started")
    else:
        stdin, stdout, stderr = ssh.exec_command("journalctl -u wg-quick@wg0 -n 10 --no-pager 2>&1")
        logs = stdout.read().decode()
        print(f"   ⚠️  Status: {status}")
        print("   Recent logs:")
        for line in logs.split('\n')[-5:]:
            if line.strip():
                print(f"   {line[:100]}")
    print("")
    
    # Verify
    print("5️⃣ Verifying WireGuard...")
    stdin, stdout, stderr = ssh.exec_command("wg show")
    wg_output = stdout.read().decode().strip()
    if wg_output:
        print("   WireGuard Status:")
        for line in wg_output.split('\n')[:5]:
            if line.strip():
                print(f"   {line}")
    else:
        print("   ⚠️  WireGuard interface not showing")
    
    stdin, stdout, stderr = ssh.exec_command("ip addr show wg0 2>&1")
    if_output = stdout.read().decode().strip()
    if "10.7.0.1" in if_output:
        print("   ✅ Interface wg0 is up with IP 10.7.0.1")
    else:
        print(f"   ⚠️  Interface status: {if_output[:100]}")
    print("")
    
    # Check port
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn 2>/dev/null | grep ':51820' || ss -tulpn 2>/dev/null | grep ':51820'")
    port_check = stdout.read().decode().strip()
    if port_check:
        print(f"   ✅ Port 51820 is listening")
    else:
        print("   ⚠️  Port 51820 not listening")
    print("")
    
    print("=" * 70)
    print("✅ WIREGUARD SETUP COMPLETE")
    print("=" * 70)
    print("")
    print(f"📋 WireGuard Public Key: {public_key}")
    print("   (Use this to generate client configs)")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

