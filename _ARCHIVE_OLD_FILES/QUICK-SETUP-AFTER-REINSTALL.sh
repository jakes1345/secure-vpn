#!/bin/bash
# ============================================
# QUICK SETUP AFTER REINSTALL
# Run this immediately after VPS reinstall
# ============================================

set -e

echo "=========================================="
echo "🚀 QUICK VPS SETUP AFTER REINSTALL"
echo "=========================================="
echo ""

# Check if root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# ============================================
# STEP 1: Update System
# ============================================
echo "1️⃣ Updating system..."
apt-get update -qq
apt-get upgrade -y -qq
echo "   ✅ System updated"
echo ""

# ============================================
# STEP 2: Install Essential Packages
# ============================================
echo "2️⃣ Installing essential packages..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    iptables \
    iptables-persistent \
    openssh-server \
    openvpn \
    python3 \
    python3-pip \
    curl \
    wget \
    git \
    -qq
echo "   ✅ Packages installed"
echo ""

# ============================================
# STEP 3: Disable UFW Completely
# ============================================
echo "3️⃣ Disabling UFW..."
echo 'ENABLED=no' > /etc/ufw/ufw.conf
echo 'ENABLED=no' > /etc/default/ufw
systemctl disable ufw 2>/dev/null || true
systemctl stop ufw 2>/dev/null || true
echo "   ✅ UFW disabled"
echo ""

# ============================================
# STEP 4: Configure Firewall (iptables)
# ============================================
echo "4️⃣ Configuring firewall..."

# Reset iptables
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Set ACCEPT first
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Add SSH rule FIRST (highest priority)
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT
iptables -I INPUT 2 -i lo -j ACCEPT
iptables -I INPUT 3 -m state --state ESTABLISHED,RELATED -j ACCEPT

# Add other essential rules
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p udp --dport 1194 -j ACCEPT
iptables -A INPUT -p icmp -j ACCEPT

# Set DROP policy last
iptables -P INPUT DROP
iptables -P FORWARD DROP

# Save rules
mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4

echo "   ✅ Firewall configured"
echo ""

# ============================================
# STEP 5: Create Boot Scripts
# ============================================
echo "5️⃣ Creating boot scripts..."

# Network script
cat > /etc/network/if-pre-up.d/iptables-load << 'EOF'
#!/bin/sh
iptables-restore < /etc/iptables/rules.v4 2>/dev/null
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT 2>/dev/null
exit 0
EOF
chmod +x /etc/network/if-pre-up.d/iptables-load

# rc.local
cat > /etc/rc.local << 'EOF'
#!/bin/bash
sleep 3
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT 2>/dev/null
iptables-save > /etc/iptables/rules.v4 2>/dev/null
exit 0
EOF
chmod +x /etc/rc.local

# Systemd service
mkdir -p /etc/systemd/system
cat > /etc/systemd/system/ssh-firewall-fix.service << 'EOF'
[Unit]
Description=Ensure SSH Firewall Rule on Boot
After=network.target
Before=ssh.service sshd.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'iptables-restore < /etc/iptables/rules.v4 2>/dev/null; iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT; iptables-save > /etc/iptables/rules.v4'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
systemctl enable ssh-firewall-fix.service

echo "   ✅ Boot scripts created"
echo ""

# ============================================
# STEP 6: Fix DNS
# ============================================
echo "6️⃣ Configuring DNS..."
rm -f /etc/resolv.conf
cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF
chattr +i /etc/resolv.conf 2>/dev/null || true
echo "   ✅ DNS configured"
echo ""

# ============================================
# STEP 7: Enable SSH Service
# ============================================
echo "7️⃣ Enabling SSH service..."
systemctl enable ssh
systemctl start ssh
echo "   ✅ SSH service enabled"
echo ""

# ============================================
# VERIFICATION
# ============================================
echo "=========================================="
echo "🔍 VERIFICATION"
echo "=========================================="
echo ""

iptables -L INPUT -n | grep "22\|ssh" && echo "✅ SSH rule in iptables" || echo "❌ SSH rule missing"
[ -f /etc/iptables/rules.v4 ] && echo "✅ Rules file exists" || echo "❌ Rules file missing"
[ -f /etc/network/if-pre-up.d/iptables-load ] && echo "✅ Network script exists" || echo "❌ Network script missing"
[ -f /etc/rc.local ] && echo "✅ rc.local exists" || echo "❌ rc.local missing"
systemctl is-enabled ssh >/dev/null && echo "✅ SSH service enabled" || echo "❌ SSH service not enabled"
grep -q "8.8.8.8" /etc/resolv.conf && echo "✅ DNS configured" || echo "❌ DNS not configured"

echo ""
echo "=========================================="
echo "✅ BASIC SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "   1. Configure OVH Edge Network Firewall"
echo "      → Bare Metal Cloud → IP → 15.204.11.19 → Firewall tab"
echo "      → Add rule: TCP port 22, Authorize, Priority 1"
echo ""
echo "   2. Deploy VPN server and web portal"
echo "      → Use deploy scripts from your PC"
echo ""
echo "   3. Test SSH from your PC"
echo "      → ssh root@15.204.11.19"
echo ""

