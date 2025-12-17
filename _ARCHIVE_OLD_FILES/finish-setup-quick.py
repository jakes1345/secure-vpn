#!/usr/bin/env python3
"""Quick finish of VPN setup"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("🚀 Finishing VPN setup...\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

commands = [
    (f"cd {VPN_DIR} && bash generate-certs.sh", "Generate certificates"),
    (f"cd {VPN_DIR} && bash setup-routing.sh", "Setup routing"),
    (f"cd {VPN_DIR} && python3 vpn-manager.py set-server-ip {VPS_IP}", "Set server IP"),
    (f"cd {VPN_DIR} && python3 vpn-manager.py init", "Initialize VPN"),
    ("systemctl daemon-reload", "Reload systemd"),
    ("systemctl enable secure-vpn secure-vpn-download", "Enable services"),
    ("systemctl start secure-vpn", "Start VPN"),
    ("sleep 2 && systemctl start secure-vpn-download", "Start download server"),
    ("systemctl status secure-vpn --no-pager | head -8", "Check VPN status"),
    ("netstat -tulpn | grep -E '(1194|8081)' || echo 'Checking ports...'", "Check ports"),
]

for cmd, desc in commands:
    print(f"  → {desc}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=120)
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    if output.strip():
        print(output[:300])
    print()

print("="*50)
print("✅ Setup complete!")
print(f"🌐 Download Server: http://{VPS_IP}:8081")
print("="*50)

ssh.close()

