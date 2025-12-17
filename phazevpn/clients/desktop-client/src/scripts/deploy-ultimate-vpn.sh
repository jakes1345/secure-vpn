#!/bin/bash

# 🔥 Ultimate VPN Deployment Script
# Deploys WireGuard + Shadowsocks + V2Ray + PhazeVPN Protocol

set -e

echo "=========================================="
echo "🚀 Ultimate VPN Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt-get update -qq

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
apt-get install -y \
    wireguard \
    wireguard-tools \
    iptables \
    iproute2 \
    curl \
    wget \
    build-essential

# Install Shadowsocks
echo -e "${YELLOW}📦 Installing Shadowsocks...${NC}"
if ! command -v ss-server &> /dev/null; then
    apt-get install -y shadowsocks-libev
fi

# Install V2Ray (optional - skip if fails)
echo -e "${YELLOW}📦 Installing V2Ray (optional)...${NC}"
if ! command -v v2ray &> /dev/null; then
    if bash <(curl -L https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh) 2>/dev/null; then
        echo -e "${GREEN}✅ V2Ray installed${NC}"
    else
        echo -e "${YELLOW}⚠️  V2Ray installation skipped (optional)${NC}"
    fi
fi

# Build Go VPN server
echo -e "${YELLOW}🔨 Building Go VPN server...${NC}"
cd /opt/phaze-vpn/phazevpn-protocol-go
go mod download
go build -o phazevpn-server-go main.go

# Create directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p /etc/phazevpn/{wireguard,shadowsocks,v2ray}
mkdir -p /var/log/phazevpn

# Generate WireGuard keys
echo -e "${YELLOW}🔑 Generating WireGuard keys...${NC}"
if [ ! -f /etc/phazevpn/wireguard/server_private.key ]; then
    wg genkey | tee /etc/phazevpn/wireguard/server_private.key | wg pubkey > /etc/phazevpn/wireguard/server_public.key
    chmod 600 /etc/phazevpn/wireguard/server_private.key
fi

# Configure WireGuard
echo -e "${YELLOW}⚙️  Configuring WireGuard...${NC}"
cat > /etc/phazevpn/wireguard/wg0.conf <<EOF
[Interface]
PrivateKey = $(cat /etc/phazevpn/wireguard/server_private.key)
Address = 10.9.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
EOF

# Configure Shadowsocks
echo -e "${YELLOW}⚙️  Configuring Shadowsocks...${NC}"
SHADOWSOCKS_PASSWORD=$(openssl rand -base64 32)
cat > /etc/phazevpn/shadowsocks/config.json <<EOF
{
    "server": "0.0.0.0",
    "server_port": 8388,
    "password": "${SHADOWSOCKS_PASSWORD}",
    "method": "chacha20-ietf-poly1305",
    "timeout": 300
}
EOF
chmod 600 /etc/phazevpn/shadowsocks/config.json

# Configure V2Ray
echo -e "${YELLOW}⚙️  Configuring V2Ray...${NC}"
cat > /etc/phazevpn/v2ray/config.json <<EOF
{
    "log": {
        "loglevel": "warning"
    },
    "inbounds": [{
        "port": 443,
        "protocol": "vmess",
        "settings": {
            "clients": [{
                "id": "$(uuidgen)",
                "alterId": 0
            }]
        },
        "streamSettings": {
            "network": "ws",
            "wsSettings": {
                "path": "/v2ray"
            },
            "security": "tls",
            "tlsSettings": {
                "certificates": [{
                    "certificateFile": "/etc/phazevpn/v2ray/cert.pem",
                    "keyFile": "/etc/phazevpn/v2ray/key.pem"
                }]
            }
        }
    }],
    "outbounds": [{
        "protocol": "freedom",
        "settings": {}
    }]
}
EOF

# Enable IP forwarding
echo -e "${YELLOW}⚙️  Enabling IP forwarding...${NC}"
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Create systemd services
echo -e "${YELLOW}📝 Creating systemd services...${NC}"

# PhazeVPN Go Server
cat > /etc/systemd/system/phazevpn-go.service <<EOF
[Unit]
Description=PhazeVPN Protocol Server (Go)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phaze-vpn/phazevpn-protocol-go
ExecStart=/opt/phaze-vpn/phazevpn-protocol-go/phazevpn-server-go -host 0.0.0.0 -port 51820 -network 10.9.0.0/24
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# WireGuard
cat > /etc/systemd/system/wg-quick@wg0.service <<EOF
[Unit]
Description=WireGuard via wg-quick(8) for wg0
Documentation=man:wg-quick(8)
Documentation=man:wg(8)
After=network-online.target nss-lookup.target
Wants=network-online.target nss-lookup.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/wg-quick up wg0
ExecStop=/usr/bin/wg-quick down wg0

[Install]
WantedBy=multi-user.target
EOF

# Shadowsocks
cat > /etc/systemd/system/shadowsocks-phazevpn.service <<EOF
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

# Reload systemd
systemctl daemon-reload

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
systemctl enable phazevpn-go.service
systemctl enable wg-quick@wg0.service
systemctl enable shadowsocks-phazevpn.service

systemctl start phazevpn-go.service
systemctl start wg-quick@wg0.service
systemctl start shadowsocks-phazevpn.service

# Show status
echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Service Status:"
systemctl status phazevpn-go.service --no-pager -l
echo ""
echo "WireGuard Status:"
wg show
echo ""
echo -e "${YELLOW}📝 Save these credentials:${NC}"
echo "Shadowsocks Password: ${SHADOWSOCKS_PASSWORD}"
echo "WireGuard Public Key: $(cat /etc/phazevpn/wireguard/server_public.key)"
echo ""
echo -e "${GREEN}🔥 Ultimate VPN is now running!${NC}"

