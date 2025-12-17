#!/bin/bash
# Quick fix for SSH - RUN THIS IN VPS CONSOLE (not via SSH!)

echo "=========================================="
echo "🔧 QUICK SSH FIX"
echo "=========================================="
echo ""

# Allow SSH
echo "1. Allowing SSH..."
ufw allow 22/tcp
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT
iptables -I INPUT 2 -p tcp --dport 22 -m state --state ESTABLISHED,RELATED -j ACCEPT
echo "   ✅ SSH allowed"

# Save rules
echo ""
echo "2. Saving firewall rules..."
mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4
echo "   ✅ Rules saved"

# Restart SSH
echo ""
echo "3. Restarting SSH..."
systemctl restart sshd
systemctl enable sshd
echo "   ✅ SSH restarted"

# Check status
echo ""
echo "4. SSH Status:"
systemctl status sshd --no-pager | head -5

echo ""
echo "=========================================="
echo "✅ SSH SHOULD WORK NOW"
echo "=========================================="
echo ""
echo "Test from your PC:"
echo "  ssh root@15.204.11.19"
echo ""

