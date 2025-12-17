#!/bin/bash
# Fix SSH on VPS - Run this FROM VPS CONSOLE (not SSH!)

echo "=========================================="
echo "🔧 FIXING SSH ON VPS"
echo "=========================================="
echo ""

# Allow SSH in firewall
echo "1. Allowing SSH in firewall..."
ufw allow 22/tcp
iptables -I INPUT -p tcp --dport 22 -j ACCEPT
iptables -I INPUT -p tcp --dport 22 -m state --state ESTABLISHED,RELATED -j ACCEPT
echo "   ✅ SSH allowed"

# Check fail2ban
echo ""
echo "2. Checking fail2ban..."
if systemctl is-active --quiet fail2ban; then
    echo "   fail2ban is running"
    fail2ban-client set sshd unbanip $(curl -s ifconfig.me) 2>/dev/null || echo "   Couldn't unban IP"
else
    echo "   fail2ban not running"
fi

# Restart SSH
echo ""
echo "3. Restarting SSH service..."
systemctl restart sshd
systemctl restart ssh
systemctl enable sshd
echo "   ✅ SSH restarted"

# Save firewall rules
echo ""
echo "4. Saving firewall rules..."
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
echo "   ✅ Rules saved"

echo ""
echo "=========================================="
echo "✅ SSH SHOULD WORK NOW"
echo "=========================================="
echo ""
echo "Test from your PC:"
echo "  ssh root@15.204.11.19"

