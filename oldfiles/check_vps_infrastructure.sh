#!/bin/bash
# Check what's actually running on the VPS

echo "🔍 Checking VPS Infrastructure..."
echo "VPS: 51.91.121.135 (phazevpn.com)"
echo ""

# Check VPN server
echo "=== VPN SERVER ==="
ssh root@51.91.121.135 "systemctl status phazevpn-server 2>/dev/null || echo 'Service not found'"
ssh root@51.91.121.135 "ps aux | grep -E '(wireguard|openvpn|phazevpn)' | grep -v grep"
ssh root@51.91.121.135 "ls -lah /etc/wireguard/ 2>/dev/null || echo 'No WireGuard config'"
ssh root@51.91.121.135 "ls -lah /etc/openvpn/ 2>/dev/null || echo 'No OpenVPN config'"
echo ""

# Check certificates
echo "=== CERTIFICATES ==="
ssh root@51.91.121.135 "find /etc -name '*.crt' -o -name '*.key' -o -name '*.pem' 2>/dev/null | head -20"
echo ""

# Check email
echo "=== EMAIL SERVICE ==="
ssh root@51.91.121.135 "systemctl status postfix 2>/dev/null || echo 'Postfix not running'"
ssh root@51.91.121.135 "systemctl status dovecot 2>/dev/null || echo 'Dovecot not running'"
echo ""

# Check web portal
echo "=== WEB PORTAL ==="
ssh root@51.91.121.135 "systemctl status phazevpn-portal 2>/dev/null || echo 'Portal service not found'"
ssh root@51.91.121.135 "ps aux | grep -E '(flask|gunicorn|python.*app.py)' | grep -v grep"
ssh root@51.91.121.135 "ls -lah /root/web-portal/ 2>/dev/null || ls -lah /var/www/phazevpn/ 2>/dev/null"
echo ""

# Check what's actually listening
echo "=== LISTENING PORTS ==="
ssh root@51.91.121.135 "netstat -tlnp | grep -E '(443|80|51820|1194|5000)'"
echo ""

echo "✅ VPS audit complete"
