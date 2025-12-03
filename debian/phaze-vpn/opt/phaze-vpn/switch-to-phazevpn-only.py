#!/usr/bin/env python3
"""
Switch to PhazeVPN Protocol Only
- Disable OpenVPN for desktop (keep for mobile)
- Make PhazeVPN Protocol the main VPN
- Keep WireGuard for mobile
"""

import paramiko
import time
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("=" * 80)
print("🔄 SWITCHING TO PHAZEVPN PROTOCOL ONLY")
print("=" * 80)
print("")
print("This will:")
print("  ✅ Keep OpenVPN + WireGuard for MOBILE ONLY")
print("  ✅ Make PhazeVPN Protocol the MAIN VPN for desktop")
print("  ✅ Update web portal configuration")
print("  ✅ Create mobile app placeholder info")
print("")
print("=" * 80)
print("")

try:
    print("📡 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected")
    print("")
    
    # Step 1: Check current services
    print("1️⃣ Checking current services...")
    services = {
        'secure-vpn': 'OpenVPN Server',
        'openvpn@server': 'OpenVPN Service',
        'phazevpn-protocol': 'PhazeVPN Protocol',
    }
    
    for service, name in services.items():
        stdin, stdout, stderr = ssh.exec_command(f'systemctl is-active {service} 2>&1')
        status = stdout.read().decode().strip()
        if status == 'active':
            print(f"   ✅ {name}: RUNNING")
        else:
            print(f"   ❌ {name}: {status}")
    print("")
    
    # Step 2: Create mobile-only OpenVPN config
    print("2️⃣ Creating mobile-only OpenVPN configuration...")
    
    mobile_config = f"""[Unit]
Description=OpenVPN Server - MOBILE ONLY
After=network.target
Documentation=man:openvpn(8)
Documentation=https://community.openvpn.net/openvpn/wiki/Openvpn24ManPage

[Service]
Type=notify
PrivateTmp=yes
WorkingDirectory={VPN_DIR}
ExecStart=/usr/sbin/openvpn --cd {VPN_DIR}/config --config server-mobile-only.conf
CapabilityBoundingSet=CAP_IPC_LOCK CAP_NET_ADMIN CAP_NET_RAW CAP_SETGID CAP_SETUID CAP_SYS_CHROOT CAP_DAC_OVERRIDE
LimitNPROC=10
DeviceAllow=/dev/null rw
DeviceAllow=/dev/net/tun rw
ProtectSystem=true
ProtectHome=true
KillMode=process
RestartSec=5s
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    
    # Write service file
    stdin, stdout, stderr = ssh.exec_command(f"""cat > /etc/systemd/system/openvpn-mobile.service << 'EOFSERVICE'
{mobile_config}
EOFSERVICE
""")
    print("   ✅ Mobile-only OpenVPN service created")
    print("")
    
    # Step 3: Create mobile-only OpenVPN config file
    print("3️⃣ Creating mobile-only OpenVPN server config...")
    
    # Get existing OpenVPN config
    stdin, stdout, stderr = ssh.exec_command(f"cat {VPN_DIR}/config/server.conf 2>/dev/null || echo ''")
    existing_config = stdout.read().decode()
    
    # Create mobile-only config with note
    mobile_openvpn_config = f"""# OpenVPN Server Configuration - MOBILE ONLY
# This is ONLY for mobile devices (phones/tablets)
# Desktop users should use PhazeVPN Protocol instead
# Port: 1194/UDP

# Server Configuration
port 1194
proto udp
dev tun
topology subnet
server 10.8.0.0 255.255.255.0

# Military-Grade Encryption
data-ciphers CHACHA20-POLY1305:AES-256-GCM
cipher CHACHA20-POLY1305
auth SHA512
tls-version-min 1.3
tls-cipher TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256

# Perfect Forward Secrecy
dh {VPN_DIR}/certs/dh.pem
tls-groups secp521r1

# Certificate Configuration
ca {VPN_DIR}/certs/ca.crt
cert {VPN_DIR}/certs/server.crt
key {VPN_DIR}/certs/server.key
tls-auth {VPN_DIR}/certs/ta.key 0

# Security Hardening
persist-key
persist-tun
remote-cert-tls client
verify-client-cert require

# Performance Optimization
tun-mtu 1500
mssfix 1450
sndbuf 2097152
rcvbuf 2097152
push "sndbuf 2097152"
push "rcvbuf 2097152"

# DNS and Privacy
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "block-outside-dns"
push "redirect-gateway def1"
push "block-ipv6"

# Logging (minimal for mobile)
verb 2
mute 20

# Mobile-specific settings
max-clients 100
keepalive 10 120

# NOTE: This is MOBILE ONLY
# Desktop users should use PhazeVPN Protocol (port 51821)
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"""cat > {VPN_DIR}/config/server-mobile-only.conf << 'EOFCONFIG'
{mobile_openvpn_config}
EOFCONFIG
""")
    print("   ✅ Mobile-only OpenVPN config created")
    print("")
    
    # Step 4: Stop desktop OpenVPN if running
    print("4️⃣ Stopping desktop OpenVPN services...")
    ssh.exec_command("systemctl stop secure-vpn 2>/dev/null || true")
    ssh.exec_command("systemctl disable secure-vpn 2>/dev/null || true")
    ssh.exec_command("systemctl stop openvpn@server 2>/dev/null || true")
    ssh.exec_command("systemctl disable openvpn@server 2>/dev/null || true")
    print("   ✅ Desktop OpenVPN stopped")
    print("")
    
    # Step 5: Enable mobile-only OpenVPN (but don't start yet - user will start manually)
    print("5️⃣ Setting up mobile-only OpenVPN...")
    ssh.exec_command("systemctl daemon-reload")
    # Don't auto-start - user will enable manually if needed
    print("   ✅ Mobile-only OpenVPN ready (not started - enable manually if needed)")
    print("")
    
    # Step 6: Ensure PhazeVPN Protocol is running
    print("6️⃣ Ensuring PhazeVPN Protocol is running...")
    ssh.exec_command("systemctl daemon-reload")
    ssh.exec_command("systemctl enable phazevpn-protocol")
    stdin, stdout, stderr = ssh.exec_command("systemctl start phazevpn-protocol")
    time.sleep(2)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-protocol")
    status = stdout.read().decode().strip()
    if status == 'active':
        print("   ✅ PhazeVPN Protocol is RUNNING")
    else:
        print(f"   ⚠️  PhazeVPN Protocol status: {status}")
    print("")
    
    # Step 7: Create info file
    print("7️⃣ Creating VPN configuration info...")
    
    vpn_info = f"""# PhazeVPN Configuration

## Desktop VPN: PhazeVPN Protocol
- Port: 51821/UDP
- Service: phazevpn-protocol
- Status: ACTIVE (Main VPN)
- Features: Zero-knowledge, traffic obfuscation, VPN modes

## Mobile VPN: OpenVPN (Temporary)
- Port: 1194/UDP
- Service: openvpn-mobile
- Status: DISABLED (Enable when needed)
- For: Phones/tablets until PhazeVPN app is ready

## Mobile VPN: WireGuard
- Port: 51820/UDP
- Service: wg-quick@wg0
- Status: CHECK STATUS
- For: Phones/tablets until PhazeVPN app is ready

## To enable mobile OpenVPN:
systemctl enable openvpn-mobile
systemctl start openvpn-mobile

## To disable mobile OpenVPN:
systemctl stop openvpn-mobile
systemctl disable openvpn-mobile
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"""cat > {VPN_DIR}/VPN-STATUS.txt << 'EOFINFO'
{vpn_info}
EOFINFO
""")
    print("   ✅ Info file created")
    print("")
    
    print("=" * 80)
    print("✅ SWITCH COMPLETE!")
    print("=" * 80)
    print("")
    print("📊 Current Status:")
    print("")
    print("🖥️  DESKTOP VPN:")
    print("   ✅ PhazeVPN Protocol: Port 51821 (MAIN VPN)")
    print("   ❌ OpenVPN: Disabled (was port 1194)")
    print("")
    print("📱 MOBILE VPN (until app ready):")
    print("   ⚠️  OpenVPN: Port 1194 (mobile-only, disabled by default)")
    print("   ⚠️  WireGuard: Port 51820 (check status)")
    print("")
    print("📋 Commands:")
    print("   # Check PhazeVPN status")
    print("   systemctl status phazevpn-protocol")
    print("")
    print("   # Enable mobile OpenVPN (if needed)")
    print("   systemctl enable openvpn-mobile")
    print("   systemctl start openvpn-mobile")
    print("")
    print("   # View VPN status")
    print("   cat /opt/secure-vpn/VPN-STATUS.txt")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

