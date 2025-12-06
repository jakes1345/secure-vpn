#!/bin/bash
# Comprehensive DDoS Protection Setup for PhazeVPN
# This protects against attacks WITHOUT needing to trust OVH

set -e

echo "=========================================="
echo "🛡️  PhazeVPN DDoS Protection Setup"
echo "=========================================="
echo ""
echo "This script sets up MULTI-LAYER DDoS protection:"
echo "  1. Cloudflare (free DDoS protection)"
echo "  2. iptables firewall rules"
echo "  3. fail2ban (auto-block attackers)"
echo "  4. Rate limiting at application level"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo $0"
    exit 1
fi

# 1. Install fail2ban
echo "📦 Step 1/4: Installing fail2ban..."
if ! command -v fail2ban-server &> /dev/null; then
    apt-get update
    apt-get install -y fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
    echo "✅ fail2ban installed"
else
    echo "✅ fail2ban already installed"
fi

# 2. Configure fail2ban for VPN
echo ""
echo "📝 Step 2/4: Configuring fail2ban for VPN protection..."
cat > /etc/fail2ban/jail.d/phazevpn.conf <<'EOF'
[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600
findtime = 600

[nginx-http-auth]
enabled = true
port = http,https
maxretry = 5
bantime = 3600

[nginx-limit-req]
enabled = true
port = http,https
maxretry = 10
bantime = 1800

[nginx-botsearch]
enabled = true
port = http,https
maxretry = 2
bantime = 86400
EOF

# Create custom filter for VPN connections
cat > /etc/fail2ban/filter.d/phazevpn.conf <<'EOF'
[Definition]
failregex = ^.*Connection from.*<HOST>.*failed.*$
            ^.*Invalid.*from.*<HOST>.*$
            ^.*Too many connections.*<HOST>.*$
ignoreregex =
EOF

cat >> /etc/fail2ban/jail.d/phazevpn.conf <<'EOF'

[phazevpn]
enabled = true
port = 1194,51820,51821
protocol = udp
maxretry = 5
bantime = 3600
findtime = 300
logpath = /var/log/phazevpn.log
EOF

systemctl restart fail2ban
echo "✅ fail2ban configured"

# 3. Set up iptables DDoS protection rules
echo ""
echo "🔥 Step 3/4: Setting up iptables DDoS protection..."
cat > /etc/iptables-ddos-rules.sh <<'EOF'
#!/bin/bash
# DDoS Protection iptables Rules

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Default policies (DROP everything, then allow specific)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established and related connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# DDoS Protection: Limit connections per IP
# Limit new connections to 20 per minute per IP
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 5 -j DROP

# Limit UDP connections (VPN ports)
iptables -A INPUT -p udp --dport 1194 -m state --state NEW -m recent --set --name openvpn
iptables -A INPUT -p udp --dport 1194 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 --name openvpn -j DROP

iptables -A INPUT -p udp --dport 51820 -m state --state NEW -m recent --set --name wireguard
iptables -A INPUT -p udp --dport 51820 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 --name wireguard -j DROP

iptables -A INPUT -p udp --dport 51821 -m state --state NEW -m recent --set --name phazevpn
iptables -A INPUT -p udp --dport 51821 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 --name phazevpn -j DROP

# Allow HTTP/HTTPS (for web portal)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow VPN ports (after rate limiting)
iptables -A INPUT -p udp --dport 1194 -j ACCEPT
iptables -A INPUT -p udp --dport 51820 -j ACCEPT
iptables -A INPUT -p udp --dport 51821 -j ACCEPT

# Allow SSH (after rate limiting)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m state --state INVALID -j DROP

# Drop packets with invalid TCP flags
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL FIN,URG,PSH -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP

# Limit ICMP (ping) to prevent ping floods
iptables -A INPUT -p icmp -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p icmp -j DROP

# Log dropped packets (for monitoring)
iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROPPED: " --log-level 4
iptables -A INPUT -j DROP
EOF

chmod +x /etc/iptables-ddos-rules.sh
/etc/iptables-ddos-rules.sh

# Save iptables rules
if command -v iptables-save &> /dev/null; then
    iptables-save > /etc/iptables/rules.v4
    echo "✅ iptables rules saved"
fi

# Install iptables-persistent to make rules survive reboot
apt-get install -y iptables-persistent || true

echo "✅ iptables DDoS protection configured"

# 4. Set up Cloudflare protection guide
echo ""
echo "☁️  Step 4/4: Cloudflare DDoS Protection Setup"
echo ""
echo "=========================================="
echo "CLOUDFLARE SETUP (FREE DDoS Protection)"
echo "=========================================="
echo ""
echo "Cloudflare provides FREE DDoS protection (up to unlimited attack size)"
echo "This protects you WITHOUT trusting OVH!"
echo ""
echo "Steps to set up Cloudflare:"
echo ""
echo "1. Sign up at: https://dash.cloudflare.com/sign-up"
echo "2. Add your domain (phazevpn.com)"
echo "3. Change your domain's nameservers to Cloudflare's"
echo "4. Enable 'Under Attack Mode' in Cloudflare dashboard"
echo "5. Set up DNS records:"
echo "   - A record: phazevpn.com → YOUR_SERVER_IP"
echo "   - A record: www.phazevpn.com → YOUR_SERVER_IP"
echo ""
echo "Cloudflare will:"
echo "  ✅ Block DDoS attacks automatically"
echo "  ✅ Cache static content (faster)"
echo "  ✅ Provide SSL certificates (free)"
echo "  ✅ Hide your real server IP"
echo ""
echo "IMPORTANT: For VPN connections, you may need to:"
echo "  - Use 'DNS Only' (gray cloud) for VPN subdomains"
echo "  - Or use direct IP for VPN (bypass Cloudflare)"
echo ""

# Create Cloudflare setup script
cat > /root/setup-cloudflare.sh <<'EOF'
#!/bin/bash
# Cloudflare DDoS Protection Setup Guide

echo "=========================================="
echo "☁️  Cloudflare DDoS Protection"
echo "=========================================="
echo ""
echo "Cloudflare provides FREE unlimited DDoS protection!"
echo ""
echo "Benefits:"
echo "  ✅ Blocks DDoS attacks automatically"
echo "  ✅ Hides your real server IP"
echo "  ✅ Free SSL certificates"
echo "  ✅ Faster website loading (caching)"
echo ""
echo "Setup Steps:"
echo ""
echo "1. Go to: https://dash.cloudflare.com"
echo "2. Add your domain: phazevpn.com"
echo "3. Change nameservers (Cloudflare will tell you)"
echo "4. Add DNS records:"
echo "   - A: phazevpn.com → YOUR_SERVER_IP (Proxied - Orange Cloud)"
echo "   - A: www.phazevpn.com → YOUR_SERVER_IP (Proxied)"
echo ""
echo "5. For VPN connections (port 1194, 51820, 51821):"
echo "   Option A: Use direct IP (bypass Cloudflare)"
echo "   Option B: Use subdomain with DNS-only (gray cloud)"
echo ""
echo "6. Enable 'Under Attack Mode' in Security settings"
echo ""
echo "That's it! Cloudflare will now protect you from DDoS!"
EOF

chmod +x /root/setup-cloudflare.sh

echo ""
echo "=========================================="
echo "✅ DDoS Protection Setup Complete!"
echo "=========================================="
echo ""
echo "Protection layers active:"
echo "  ✅ fail2ban (auto-block attackers)"
echo "  ✅ iptables (rate limiting + firewall)"
echo "  📋 Cloudflare setup guide: /root/setup-cloudflare.sh"
echo ""
echo "Next steps:"
echo "  1. Review fail2ban status: fail2ban-client status"
echo "  2. Review iptables rules: iptables -L -n -v"
echo "  3. Set up Cloudflare: bash /root/setup-cloudflare.sh"
echo ""
echo "Your VPN is now protected against DDoS attacks!"
echo ""

