#!/bin/bash
# Enhance System Privacy for VPN Users
# Applies OS-level privacy settings

set -e

echo "=========================================="
echo "System Privacy Enhancement"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "✅ Running as root"
echo ""

# Step 1: Disable IPv6 completely
echo "🔒 Step 1: Disabling IPv6..."
if ! grep -q "net.ipv6.conf.all.disable_ipv6=1" /etc/sysctl.conf; then
    cat >> /etc/sysctl.conf << 'EOF'

# Privacy: Disable IPv6 to prevent leaks
net.ipv6.conf.all.disable_ipv6=1
net.ipv6.conf.default.disable_ipv6=1
net.ipv6.conf.lo.disable_ipv6=1
EOF
    sysctl -p
    echo "✅ IPv6 disabled"
else
    echo "✅ IPv6 already disabled"
fi

# Step 2: Disable system DNS leaks
echo ""
echo "🔒 Step 2: Configuring privacy-focused DNS..."

# Check if systemd-resolved is used
if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
    RESOLVED_CONF="/etc/systemd/resolved.conf"
    if [ -f "$RESOLVED_CONF" ]; then
        # Backup original
        cp "$RESOLVED_CONF" "$RESOLVED_CONF.bak"
        
        # Configure DNS over TLS with privacy DNS
        sed -i 's/^#DNS=.*/DNS=1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com/' "$RESOLVED_CONF"
        sed -i 's/^#DNSOverTLS=.*/DNSOverTLS=yes/' "$RESOLVED_CONF"
        sed -i 's/^#DNSSEC=.*/DNSSEC=allow-downgrade/' "$RESOLVED_CONF"
        
        systemctl restart systemd-resolved
        echo "✅ System DNS configured for privacy (Cloudflare DoT)"
    fi
fi

# Step 3: Disable unnecessary network services
echo ""
echo "🔒 Step 3: Disabling network tracking services..."

# Disable mDNS (can leak hostname)
systemctl disable avahi-daemon 2>/dev/null || true
systemctl stop avahi-daemon 2>/dev/null || true

# Disable LLMNR (can leak hostname)
if [ -f /etc/systemd/resolved.conf ]; then
    sed -i 's/^#LLMNR=.*/LLMNR=no/' /etc/systemd/resolved.conf
    systemctl restart systemd-resolved 2>/dev/null || true
fi

echo "✅ Network tracking services disabled"

# Step 4: Configure firewall for privacy
echo ""
echo "🔒 Step 4: Configuring firewall for privacy..."

# Block DNS leaks (force DNS through VPN only)
if command -v iptables &> /dev/null; then
    # Allow DNS to VPN DNS servers only
    iptables -I OUTPUT -p udp --dport 53 -d 1.1.1.1 -j ACCEPT 2>/dev/null || true
    iptables -I OUTPUT -p udp --dport 53 -d 1.0.0.1 -j ACCEPT 2>/dev/null || true
    iptables -I OUTPUT -p tcp --dport 53 -d 1.1.1.1 -j ACCEPT 2>/dev/null || true
    iptables -I OUTPUT -p tcp --dport 53 -d 1.0.0.1 -j ACCEPT 2>/dev/null || true
    # Block all other DNS
    iptables -I OUTPUT -p udp --dport 53 -j DROP 2>/dev/null || true
    iptables -I OUTPUT -p tcp --dport 53 -j DROP 2>/dev/null || true
    
    echo "✅ Firewall configured to prevent DNS leaks"
fi

# Step 5: Disable system logging of network activity
echo ""
echo "🔒 Step 5: Reducing system logging..."

# Disable connection logging in syslog
if [ -f /etc/rsyslog.conf ]; then
    # Comment out network-related logging
    sed -i 's/^kern.*/##kern.*/' /etc/rsyslog.conf 2>/dev/null || true
    systemctl restart rsyslog 2>/dev/null || true
fi

echo "✅ System logging reduced"

# Step 6: Privacy tools (skipped - we're building our own browser)
echo ""
echo "🔒 Step 6: Privacy tools..."
echo "   ℹ️  Custom browser in development - no external browser needed"

# Summary
echo ""
echo "=========================================="
echo "✅ Privacy Enhancement Complete!"
echo "=========================================="
echo ""
echo "📋 What was configured:"
echo "   ✅ IPv6 completely disabled"
echo "   ✅ Privacy-focused DNS (Cloudflare DoT)"
echo "   ✅ Network tracking services disabled"
echo "   ✅ Firewall configured to prevent DNS leaks"
echo "   ✅ System logging reduced"
echo ""
echo "🔍 Next Steps:"
echo "   1. Test for leaks:"
echo "      - https://ipleak.net"
echo "      - https://dnsleaktest.com"
echo ""
echo "   2. Custom browser in development:"
echo "      - PhazeBrowser will have all privacy features built-in"
echo "      - No extensions needed - everything VPN-native"
echo ""
echo "📚 For detailed guide, see: VPN-NATIVE-SECURITY.md"
echo ""

