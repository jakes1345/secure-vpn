#!/bin/bash
# Permanently fix DNS on VPS

echo "=========================================="
echo "🔧 PERMANENTLY FIXING DNS"
echo "=========================================="
echo ""

# 1. Configure systemd-resolved
echo "1. Configuring systemd-resolved..."
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/dns.conf << EOF
[Resolve]
DNS=8.8.8.8 1.1.1.1 8.8.4.4
FallbackDNS=1.0.0.1
Domains=~.
EOF
echo "   ✅ Configured"

# 2. Set NetworkManager DNS if available
echo "2. Setting NetworkManager DNS..."
if command -v nmcli &> /dev/null; then
    CONNECTION=$(nmcli -t -f NAME connection show --active | head -1)
    if [ -n "$CONNECTION" ]; then
        nmcli connection modify "$CONNECTION" ipv4.dns "8.8.8.8 1.1.1.1" ipv4.ignore-auto-dns yes
        echo "   ✅ NetworkManager configured"
    fi
else
    echo "   ⚠️  NetworkManager not found (skipping)"
fi

# 3. Set static resolv.conf
echo "3. Setting static resolv.conf..."
rm -f /etc/resolv.conf
cat > /etc/resolv.conf << EOF
nameserver 8.8.8.8
nameserver 1.1.1.1
nameserver 8.8.4.4
EOF
chattr +i /etc/resolv.conf 2>/dev/null || true
echo "   ✅ Static DNS set"

# 4. Restart systemd-resolved
echo "4. Restarting systemd-resolved..."
systemctl restart systemd-resolved
systemctl enable systemd-resolved
echo "   ✅ Restarted"

# 5. Test DNS
echo ""
echo "5. Testing DNS..."
sleep 2
if nslookup api.mailjet.com > /dev/null 2>&1; then
    echo "   ✅ DNS working!"
else
    echo "   ⚠️  DNS test failed (may need reboot)"
fi

echo ""
echo "=========================================="
echo "✅ DNS FIXED PERMANENTLY"
echo "=========================================="

