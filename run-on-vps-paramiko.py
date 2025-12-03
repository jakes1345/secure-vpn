#!/usr/bin/env python3
"""Run Ultimate VPN setup on VPS using Paramiko"""

import paramiko
import os
from pathlib import Path
import time

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    
    raise Exception("Failed to connect to VPS")

def run_command(ssh, command, description):
    """Run command and show output"""
    print(f"  ⚙️  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status == 0:
        print(f"  ✅ Success")
        if output.strip():
            print(f"     {output.strip()[:200]}")
        return True, output
    else:
        print(f"  ❌ Failed: {error[:200]}")
        return False, error

def main():
    print("=" * 70)
    print("🚀 Ultimate VPN Setup on VPS (via Paramiko)")
    print("=" * 70)
    print(f"📍 VPS: {VPS_HOST}")
    print("=" * 70)
    print()
    
    ssh = connect_vps()
    print("✅ Connected to VPS\n")
    
    try:
        # Step 1: Install Go
        print("📋 Step 1: Installing Go 1.21+...")
        run_command(ssh,
            "cd /tmp && wget -q https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && "
            "rm -rf /usr/local/go && tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && "
            "rm go1.21.5.linux-amd64.tar.gz && "
            "/usr/local/go/bin/go version",
            "Install Go 1.21.5"
        )
        print()
        
        # Step 2: Install dependencies
        print("📋 Step 2: Installing dependencies...")
        run_command(ssh,
            "apt-get update -qq && "
            "apt-get install -y wireguard wireguard-tools shadowsocks-libev iptables iproute2 curl wget build-essential",
            "Install packages"
        )
        print()
        
        # Step 3: Build Go server
        print("📋 Step 3: Building Go VPN server...")
        run_command(ssh,
            "cd /opt/phaze-vpn/phazevpn-protocol-go && "
            "export PATH=$PATH:/usr/local/go/bin && "
            "/usr/local/go/bin/go mod tidy",
            "Tidy Go modules"
        )
        
        run_command(ssh,
            "cd /opt/phaze-vpn/phazevpn-protocol-go && "
            "export PATH=$PATH:/usr/local/go/bin && "
            "/usr/local/go/bin/go build -o phazevpn-server-go main.go && "
            "chmod +x phazevpn-server-go && "
            "ls -lh phazevpn-server-go",
            "Build Go server"
        )
        print()
        
        # Step 4: Setup WireGuard
        print("📋 Step 4: Setting up WireGuard...")
        run_command(ssh,
            "mkdir -p /etc/phazevpn/wireguard && "
            "(wg genkey | tee /etc/phazevpn/wireguard/server_private.key | wg pubkey > /etc/phazevpn/wireguard/server_public.key) && "
            "chmod 600 /etc/phazevpn/wireguard/server_private.key && "
            "echo 'WireGuard Public Key:' && cat /etc/phazevpn/wireguard/server_public.key",
            "Generate WireGuard keys"
        )
        print()
        
        # Step 5: Setup Shadowsocks
        print("📋 Step 5: Setting up Shadowsocks...")
        shadowsocks_cmd = """mkdir -p /etc/phazevpn/shadowsocks && \
SHADOWSOCKS_PASSWORD=$(openssl rand -base64 32) && \
cat > /etc/phazevpn/shadowsocks/config.json <<'EOF'
{
    "server": "0.0.0.0",
    "server_port": 8388,
    "password": "${SHADOWSOCKS_PASSWORD}",
    "method": "chacha20-ietf-poly1305",
    "timeout": 300
}
EOF
chmod 600 /etc/phazevpn/shadowsocks/config.json && \
echo "Shadowsocks Password: $SHADOWSOCKS_PASSWORD"
"""
        run_command(ssh, shadowsocks_cmd, "Configure Shadowsocks")
        print()
        
        # Step 6: Enable IP forwarding
        print("📋 Step 6: Enabling IP forwarding...")
        run_command(ssh,
            "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf && sysctl -p",
            "Enable IP forwarding"
        )
        print()
        
        # Step 7: Create systemd service for Go server
        print("📋 Step 7: Creating systemd service for Go server...")
        service_cmd = """cat > /etc/systemd/system/phazevpn-go.service <<'EOF'
[Unit]
Description=PhazeVPN Protocol Server (Go)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phaze-vpn/phazevpn-protocol-go
Environment="PATH=/usr/local/go/bin:/usr/bin:/bin"
ExecStart=/opt/phaze-vpn/phazevpn-protocol-go/phazevpn-server-go -host 0.0.0.0 -port 51820 -network 10.9.0.0/24
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable phazevpn-go.service && systemctl start phazevpn-go.service"""
        run_command(ssh, service_cmd, "Create and start Go server service")
        print()
        
        # Step 8: Create systemd service for Shadowsocks
        print("📋 Step 8: Creating systemd service for Shadowsocks...")
        shadowsocks_service = """cat > /etc/systemd/system/shadowsocks-phazevpn.service <<'EOF'
[Unit]
Description=Shadowsocks Obfuscation Layer
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/ss-server -c /etc/phazevpn/shadowsocks/config.json
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable shadowsocks-phazevpn.service && systemctl start shadowsocks-phazevpn.service"""
        run_command(ssh, shadowsocks_service, "Create and start Shadowsocks service")
        print()
        
        # Step 9: Verify
        print("📋 Step 9: Verifying setup...")
        time.sleep(3)
        
        verify_cmd = """echo '=== Services ===' && \
systemctl is-active phazevpn-go.service && echo '✅ PhazeVPN Go Server' || echo '❌ PhazeVPN Go Server' && \
systemctl is-active shadowsocks-phazevpn.service && echo '✅ Shadowsocks' || echo '❌ Shadowsocks' && \
echo '' && \
echo '=== Processes ===' && \
ps aux | grep -E '[p]hazevpn-server-go|[s]s-server' | head -3 && \
echo '' && \
echo '=== Ports ===' && \
(netstat -tuln 2>/dev/null | grep -E '(51820|8388)' || ss -tuln 2>/dev/null | grep -E '(51820|8388)' || echo 'No ports listening yet') && \
echo '' && \
echo '=== Logs (last 5 lines) ===' && \
journalctl -u phazevpn-go.service -n 5 --no-pager"""
        
        success, output = run_command(ssh, verify_cmd, "Verify everything")
        print()
        print(output)
        print()
        
        print("=" * 70)
        print("✅ Setup Complete!")
        print("=" * 70)
        print()
        print("📝 Useful commands:")
        print("  Check status: systemctl status phazevpn-go.service")
        print("  View logs: journalctl -u phazevpn-go.service -f")
        print("  Restart: systemctl restart phazevpn-go.service")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("✅ Connection closed")

if __name__ == "__main__":
    main()

