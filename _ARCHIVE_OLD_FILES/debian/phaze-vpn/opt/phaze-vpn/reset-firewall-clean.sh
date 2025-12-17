#!/bin/bash
# Reset firewall to clean state and add only necessary rules
# Run this in rescue mode after chroot

echo "=========================================="
echo "🧹 RESETTING FIREWALL TO CLEAN STATE..."
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

# Step 1: Stop conflicting services
echo "1️⃣ Stopping conflicting firewall services..."
systemctl stop ufw 2>/dev/null || true
systemctl stop fail2ban 2>/dev/null || true
echo "   ✅ Services stopped"
echo ""

# Step 2: Reset iptables to default (ACCEPT everything)
echo "2️⃣ Resetting iptables to clean state..."
iptables -F  # Flush all rules
iptables -X  # Delete all chains
iptables -t nat -F  # Flush NAT
iptables -t nat -X  # Delete NAT chains
iptables -t mangle -F  # Flush mangle
iptables -t mangle -X  # Delete mangle chains

# Set default policies to ACCEPT (we'll add specific rules after)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
echo "   ✅ iptables reset to clean state"
echo ""

# Step 3: Add ONLY essential rules (in order)
echo "3️⃣ Adding essential firewall rules..."
echo ""

# Allow loopback (always needed)
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT
echo "   ✅ Loopback allowed"

# Allow established connections (important!)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
echo "   ✅ Established connections allowed"

# Allow SSH (CRITICAL!)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
echo "   ✅ SSH (port 22) allowed"

# Allow DNS (needed for everything)
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
echo "   ✅ DNS (port 53) allowed"

# Allow HTTPS (for Mailjet API, web portal)
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
echo "   ✅ HTTPS (port 443) allowed"

# Allow HTTP (for web portal)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
echo "   ✅ HTTP (port 80) allowed"

# Allow OpenVPN (UDP 1194)
iptables -A INPUT -p udp --dport 1194 -j ACCEPT
iptables -A OUTPUT -p udp --dport 1194 -j ACCEPT
echo "   ✅ OpenVPN (port 1194) allowed"

# Allow ICMP (ping)
iptables -A INPUT -p icmp -j ACCEPT
iptables -A OUTPUT -p icmp -j ACCEPT
echo "   ✅ ICMP (ping) allowed"

# Now set default policy to DROP for INPUT (but we've allowed what we need)
iptables -P INPUT DROP
iptables -P FORWARD DROP
# OUTPUT stays ACCEPT (we want to allow outbound)
echo "   ✅ Default policies set (INPUT/FORWARD DROP, OUTPUT ACCEPT)"
echo ""

# Step 4: Disable UFW to prevent conflicts
echo "4️⃣ Disabling UFW to prevent conflicts..."
systemctl disable ufw 2>/dev/null || true
systemctl stop ufw 2>/dev/null || true
echo "   ✅ UFW disabled"
echo ""

# Step 5: Save iptables rules permanently
echo "5️⃣ Saving iptables rules permanently..."
mkdir -p /etc/iptables

# Install iptables-persistent if not installed
if ! command -v iptables-save > /dev/null; then
    echo "   Installing iptables-persistent..."
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y iptables-persistent -qq > /dev/null 2>&1
fi

# Save rules
iptables-save > /etc/iptables/rules.v4
echo "   ✅ Rules saved to /etc/iptables/rules.v4"
echo ""

# Step 6: Restart SSH
echo "6️⃣ Restarting SSH service..."
systemctl restart sshd
systemctl enable sshd
echo "   ✅ SSH restarted and enabled"
echo ""

# Step 7: Verify SSH is running
echo "7️⃣ Verifying SSH status..."
if systemctl is-active --quiet sshd; then
    echo "   ✅ SSH service is RUNNING"
else
    echo "   ⚠️  SSH service might not be running"
fi
echo ""

# Step 8: Show current rules
echo "8️⃣ Current firewall rules:"
iptables -L -n -v | head -20
echo ""

echo "=========================================="
echo "✅ FIREWALL RESET COMPLETE!"
echo "=========================================="
echo ""
echo "📋 What was done:"
echo "   ✅ Reset all firewall rules to clean state"
echo "   ✅ Disabled UFW (prevent conflicts)"
echo "   ✅ Added only essential rules:"
echo "      - SSH (22)"
echo "      - DNS (53)"
echo "      - HTTPS (443)"
echo "      - HTTP (80)"
echo "      - OpenVPN (1194)"
echo "      - ICMP (ping)"
echo "   ✅ Saved rules permanently"
echo "   ✅ Restarted SSH"
echo ""
echo "🚀 Next steps:"
echo "   1. Exit chroot: exit"
echo "   2. Reboot: reboot"
echo "   3. Wait 2-3 minutes"
echo "   4. Test SSH: ssh root@15.204.11.19"
echo "   5. If SSH works, run: python3 deploy-after-reboot.py"
echo ""

