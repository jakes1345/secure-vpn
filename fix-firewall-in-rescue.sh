#!/bin/bash
# Fix firewall in rescue mode (run after chroot)

echo "=========================================="
echo "🔧 FIXING FIREWALL IN RESCUE MODE..."
echo "=========================================="
echo ""

# Check if we're in chroot
if [ ! -f /etc/os-release ]; then
    echo "❌ ERROR: This script must be run INSIDE chroot!"
    echo ""
    echo "Steps:"
    echo "  1. Mount your disk: mount /dev/sda2 /mnt/recovery"
    echo "  2. Bind dirs: mount --bind /dev /mnt/recovery/dev (etc)"
    echo "  3. Chroot: chroot /mnt/recovery"
    echo "  4. Then run this script"
    exit 1
fi

echo "✅ In chroot, proceeding..."
echo ""

# Fix UFW
echo "1️⃣ Fixing UFW..."
ufw allow 22/tcp
ufw allow 443/tcp  # HTTPS for Mailjet
ufw allow 53/udp   # DNS
ufw allow 53/tcp   # DNS
echo "   ✅ UFW rules added"
echo ""

# Fix iptables
echo "2️⃣ Fixing iptables..."
iptables -I INPUT -p tcp --dport 22 -j ACCEPT
iptables -I INPUT -p tcp --dport 443 -j ACCEPT
iptables -I INPUT -p udp --dport 53 -j ACCEPT
iptables -I INPUT -p tcp --dport 53 -j ACCEPT
echo "   ✅ iptables rules added"
echo ""

# Save iptables permanently
echo "3️⃣ Saving iptables rules..."
if command -v iptables-save > /dev/null; then
    mkdir -p /etc/iptables
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    echo "   ✅ iptables rules saved"
else
    echo "   ⚠️  iptables-save not found, installing iptables-persistent..."
    apt-get update -qq
    apt-get install -y iptables-persistent -qq
    iptables-save > /etc/iptables/rules.v4
    echo "   ✅ iptables rules saved"
fi
echo ""

# Restart SSH
echo "4️⃣ Restarting SSH..."
systemctl restart sshd
echo "   ✅ SSH restarted"
echo ""

# Test SSH
echo "5️⃣ Testing SSH..."
if systemctl is-active --quiet sshd; then
    echo "   ✅ SSH service is running"
else
    echo "   ⚠️  SSH service might not be running"
fi
echo ""

echo "=========================================="
echo "✅ FIREWALL FIXED!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Exit chroot: exit"
echo "  2. Reboot: reboot"
echo "  3. Wait 2-3 minutes"
echo "  4. Try SSH: ssh root@15.204.11.19"
echo ""

