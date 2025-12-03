#!/bin/bash
# 🔥 Ultimate VPN - Run this directly on VPS
# SSH into VPS first: ssh root@15.204.11.19
# Then: bash <(curl -s https://raw.githubusercontent.com/your-repo/run-on-vps.sh) 
# OR: Copy this file to VPS and run: bash run-on-vps.sh

set -e

echo "=========================================="
echo "🚀 Ultimate VPN Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Step 1: Install Go 1.21+
echo -e "${YELLOW}📦 Step 1: Installing Go 1.21+...${NC}"
if ! /usr/local/go/bin/go version 2>/dev/null | grep -q "go1.2"; then
    cd /tmp
    wget -q https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
    rm -rf /usr/local/go
    tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
    rm go1.21.5.linux-amd64.tar.gz
    echo -e "${GREEN}✅ Go installed${NC}"
else
    echo -e "${GREEN}✅ Go already installed${NC}"
fi
/usr/local/go/bin/go version

# Step 2: Install dependencies
echo -e "\n${YELLOW}📦 Step 2: Installing dependencies...${NC}"
apt-get update -qq
apt-get install -y wireguard wireguard-tools shadowsocks-libev iptables iproute2 curl wget build-essential

# Step 3: Build Go server (if files exist)
echo -e "\n${YELLOW}🔨 Step 3: Building Go VPN server...${NC}"
if [ -d "/opt/phaze-vpn/phazevpn-protocol-go" ]; then
    cd /opt/phaze-vpn/phazevpn-protocol-go
    export PATH=$PATH:/usr/local/go/bin
    /usr/local/go/bin/go mod tidy
    /usr/local/go/bin/go build -o phazevpn-server-go main.go
    chmod +x phazevpn-server-go
    echo -e "${GREEN}✅ Go server built${NC}"
else
    echo -e "${RED}❌ Go server files not found at /opt/phaze-vpn/phazevpn-protocol-go${NC}"
    echo "   Upload files first using deploy-ultimate-vpn-to-vps.py"
    exit 1
fi

# Step 4: Setup WireGuard
echo -e "\n${YELLOW}⚙️  Step 4: Setting up WireGuard...${NC}"
mkdir -p /etc/phazevpn/wireguard
if [ ! -f /etc/phazevpn/wireguard/server_private.key ]; then
    wg genkey | tee /etc/phazevpn/wireguard/server_private.key | wg pubkey > /etc/phazevpn/wireguard/server_public.key
    chmod 600 /etc/phazevpn/wireguard/server_private.key
    echo -e "${GREEN}✅ WireGuard keys generated${NC}"
fi

# Step 5: Setup Shadowsocks
echo -e "\n${YELLOW}⚙️  Step 5: Setting up Shadowsocks...${NC}"
mkdir -p /etc/phazevpn/shadowsocks
if [ ! -f /etc/phazevpn/shadowsocks/config.json ]; then
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
    echo -e "${GREEN}✅ Shadowsocks configured${NC}"
    echo -e "${YELLOW}   Password: ${SHADOWSOCKS_PASSWORD}${NC}"
fi

# Step 6: Enable IP forwarding
echo -e "\n${YELLOW}⚙️  Step 6: Enabling IP forwarding...${NC}"
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p > /dev/null
echo -e "${GREEN}✅ IP forwarding enabled${NC}"

# Step 7: Create systemd services
echo -e "\n${YELLOW}📝 Step 7: Creating systemd services...${NC}"

# PhazeVPN Go Server
cat > /etc/systemd/system/phazevpn-go.service <<'EOF'
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

# Shadowsocks
cat > /etc/systemd/system/shadowsocks-phazevpn.service <<'EOF'
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

systemctl daemon-reload
echo -e "${GREEN}✅ Services created${NC}"

# Step 8: Start services
echo -e "\n${YELLOW}🚀 Step 8: Starting services...${NC}"
systemctl enable phazevpn-go.service
systemctl enable shadowsocks-phazevpn.service
systemctl start phazevpn-go.service
systemctl start shadowsocks-phazevpn.service

sleep 3

# Step 9: Verify
echo -e "\n${YELLOW}🔍 Step 9: Verifying...${NC}"
echo "Services:"
systemctl is-active phazevpn-go.service && echo "  ✅ PhazeVPN Go Server" || echo "  ❌ PhazeVPN Go Server"
systemctl is-active shadowsocks-phazevpn.service && echo "  ✅ Shadowsocks" || echo "  ❌ Shadowsocks"

echo ""
echo "Processes:"
ps aux | grep -E '[p]hazevpn-server-go|[s]s-server' | head -3

echo ""
echo "Ports:"
netstat -tuln 2>/dev/null | grep -E '(51820|8388)' || ss -tuln 2>/dev/null | grep -E '(51820|8388)' || echo "  No ports listening yet"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "📝 Useful commands:"
echo "  Check status: systemctl status phazevpn-go.service"
echo "  View logs: journalctl -u phazevpn-go.service -f"
echo "  Restart: systemctl restart phazevpn-go.service"
echo ""

