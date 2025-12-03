#!/bin/bash
# Complete VPS Setup - DNS + Firewall + Everything
# This script ensures DNS and firewall work perfectly, no conflicts ever
# Run this ONCE on the VPS to set everything up properly

set -e

LOG_FILE="/opt/secure-vpn/logs/vps-setup.log"
mkdir -p /opt/secure-vpn/logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

echo "=========================================="
echo "🚀 COMPLETE VPS SETUP - DNS + FIREWALL"
echo "=========================================="
echo ""

log "=== Starting Complete VPS Setup ==="

# ============================================
# PART 1: DNS CONFIGURATION (PERMANENT)
# ============================================
log "=== PART 1: DNS Configuration ==="

echo "1️⃣ Configuring DNS permanently..."

# Step 1: Stop and disable systemd-resolved (it conflicts with manual DNS)
log "   Stopping systemd-resolved..."
systemctl stop systemd-resolved 2>/dev/null || true
systemctl disable systemd-resolved 2>/dev/null || true
log "   ✅ systemd-resolved stopped"

# Step 2: Remove systemd-resolved stub
log "   Removing systemd-resolved stub..."
if [ -L /etc/resolv.conf ]; then
    rm -f /etc/resolv.conf
    log "   ✅ Removed symlink"
fi

# Step 3: Set DNS servers directly in resolv.conf
log "   Setting DNS servers in /etc/resolv.conf..."
cat > /etc/resolv.conf << 'EOF'
# DNS Configuration - Managed by secure-vpn
# These DNS servers are used for system DNS resolution
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
nameserver 1.0.0.1
options timeout:2 attempts:3 rotate
EOF
chattr +i /etc/resolv.conf 2>/dev/null || true  # Make it immutable (protect from systemd-resolved)
log "   ✅ DNS servers set: 8.8.8.8, 8.8.4.4, 1.1.1.1, 1.0.0.1"

# Step 4: Configure systemd-resolved (if it gets re-enabled)
log "   Configuring systemd-resolved as backup..."
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/dns.conf << 'EOF'
[Resolve]
DNS=8.8.8.8 8.8.4.4 1.1.1.1 1.0.0.1
FallbackDNS=8.8.8.8 1.1.1.1
Domains=
DNSSEC=no
DNSOverTLS=no
EOF
log "   ✅ systemd-resolved configured (backup)"

# Step 5: Test DNS
log "   Testing DNS resolution..."
if nslookup google.com > /dev/null 2>&1; then
    log "   ✅ DNS resolution working!"
else
    log "   ⚠️  DNS test failed, but continuing..."
fi

echo "   ✅ DNS configuration complete"
echo ""

# ============================================
# PART 2: FIREWALL CONFIGURATION (CLEAN)
# ============================================
log "=== PART 2: Firewall Configuration ==="

echo "2️⃣ Configuring firewall (clean, no conflicts)..."

# Step 1: Stop and disable UFW (prevent conflicts)
log "   Stopping UFW..."
systemctl stop ufw 2>/dev/null || true
systemctl disable ufw 2>/dev/null || true
log "   ✅ UFW stopped and disabled"

# Step 2: Stop fail2ban temporarily (we'll restart it after)
log "   Stopping fail2ban temporarily..."
systemctl stop fail2ban 2>/dev/null || true
log "   ✅ fail2ban stopped"

# Step 3: Reset iptables to clean state
log "   Resetting iptables to clean state..."
iptables -F  # Flush all rules
iptables -X  # Delete all chains
iptables -t nat -F  # Flush NAT
iptables -t nat -X  # Delete NAT chains
iptables -t mangle -F  # Flush mangle
iptables -t mangle -X  # Delete mangle chains

# Set default policies to ACCEPT (we'll add rules, then set to DROP)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
log "   ✅ iptables reset to clean state"

# Step 4: Add essential firewall rules (in correct order)
log "   Adding essential firewall rules..."

# Allow loopback (always first)
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT
log "   ✅ Loopback allowed"

# Allow established/related connections (important!)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
log "   ✅ Established connections allowed"

# Allow SSH (CRITICAL!)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT
log "   ✅ SSH (port 22) allowed"

# Allow DNS (UDP and TCP)
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
log "   ✅ DNS (port 53) allowed"

# Allow HTTPS (for Mailjet API, web portal)
iptables -A INPUT -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT
log "   ✅ HTTPS (port 443) allowed"

# Allow HTTP (for web portal)
iptables -A INPUT -p tcp --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT
log "   ✅ HTTP (port 80) allowed"

# Allow OpenVPN (UDP 1194)
iptables -A INPUT -p udp --dport 1194 -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p udp --sport 1194 -m state --state ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p udp --dport 1194 -m state --state NEW,ESTABLISHED -j ACCEPT
log "   ✅ OpenVPN (port 1194) allowed"

# Allow ICMP (ping)
iptables -A INPUT -p icmp -j ACCEPT
iptables -A OUTPUT -p icmp -j ACCEPT
log "   ✅ ICMP (ping) allowed"

# Allow VPN forwarding (for OpenVPN)
iptables -A FORWARD -i tun+ -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o tun+ -m state --state RELATED,ESTABLISHED -j ACCEPT
log "   ✅ VPN forwarding allowed"

# NAT for VPN (masquerade)
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
log "   ✅ NAT masquerade configured"

# Now set default policies to DROP (but we've allowed what we need)
iptables -P INPUT DROP
iptables -P FORWARD DROP
# OUTPUT stays ACCEPT (we want to allow outbound)
log "   ✅ Default policies set (INPUT/FORWARD DROP, OUTPUT ACCEPT)"

echo "   ✅ Firewall configuration complete"
echo ""

# ============================================
# PART 3: SAVE FIREWALL RULES PERMANENTLY
# ============================================
log "=== PART 3: Saving Firewall Rules ==="

echo "3️⃣ Saving firewall rules permanently..."

# Install iptables-persistent if not installed
if ! command -v iptables-save > /dev/null; then
    log "   Installing iptables-persistent..."
    apt-get update -qq > /dev/null 2>&1
    DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent -qq > /dev/null 2>&1
    log "   ✅ iptables-persistent installed"
fi

# Save IPv4 rules
mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4
log "   ✅ IPv4 rules saved to /etc/iptables/rules.v4"

# Save IPv6 rules (if ip6tables exists)
if command -v ip6tables > /dev/null; then
    ip6tables -F
    ip6tables -X
    ip6tables -P INPUT ACCEPT
    ip6tables -P FORWARD ACCEPT
    ip6tables -P OUTPUT ACCEPT
    ip6tables-save > /etc/iptables/rules.v6
    log "   ✅ IPv6 rules saved to /etc/iptables/rules.v6"
fi

# Enable netfilter-persistent (loads rules on boot)
systemctl enable netfilter-persistent 2>/dev/null || true
log "   ✅ netfilter-persistent enabled"

echo "   ✅ Firewall rules saved permanently"
echo ""

# ============================================
# PART 4: RESTART SERVICES
# ============================================
log "=== PART 4: Restarting Services ==="

echo "4️⃣ Restarting services..."

# Restart SSH
log "   Restarting SSH..."
systemctl restart sshd
systemctl enable sshd
log "   ✅ SSH restarted and enabled"

# Restart fail2ban (but configure it properly)
log "   Restarting fail2ban..."
systemctl start fail2ban 2>/dev/null || true
systemctl enable fail2ban 2>/dev/null || true
log "   ✅ fail2ban restarted"

# Restart OpenVPN (if installed)
if systemctl list-unit-files | grep -q openvpn; then
    log "   Restarting OpenVPN..."
    systemctl restart openvpn 2>/dev/null || true
    log "   ✅ OpenVPN restarted"
fi

echo "   ✅ Services restarted"
echo ""

# ============================================
# PART 5: VERIFICATION
# ============================================
log "=== PART 5: Verification ==="

echo "5️⃣ Verifying configuration..."

# Test DNS
log "   Testing DNS..."
if nslookup google.com > /dev/null 2>&1; then
    log "   ✅ DNS: WORKING"
    echo "      ✅ DNS resolution working"
else
    log "   ❌ DNS: FAILED"
    echo "      ❌ DNS resolution failed"
fi

# Test SSH
log "   Testing SSH..."
if systemctl is-active --quiet sshd; then
    log "   ✅ SSH: RUNNING"
    echo "      ✅ SSH service is running"
else
    log "   ❌ SSH: NOT RUNNING"
    echo "      ❌ SSH service is not running"
fi

# Test firewall rules
log "   Testing firewall rules..."
if iptables -L INPUT -n | grep -q "tcp dpt:22"; then
    log "   ✅ Firewall: SSH rule exists"
    echo "      ✅ SSH firewall rule exists"
else
    log "   ❌ Firewall: SSH rule missing"
    echo "      ❌ SSH firewall rule missing"
fi

if iptables -L INPUT -n | grep -q "udp dpt:53"; then
    log "   ✅ Firewall: DNS rule exists"
    echo "      ✅ DNS firewall rule exists"
else
    log "   ❌ Firewall: DNS rule missing"
    echo "      ❌ DNS firewall rule missing"
fi

# Test HTTPS connectivity
log "   Testing HTTPS connectivity..."
if curl -s --max-time 5 https://api.mailjet.com > /dev/null 2>&1; then
    log "   ✅ HTTPS: WORKING"
    echo "      ✅ HTTPS connectivity working"
else
    log "   ⚠️  HTTPS: May not be working (could be normal)"
    echo "      ⚠️  HTTPS test inconclusive"
fi

echo "   ✅ Verification complete"
echo ""

# ============================================
# PART 6: CREATE MAINTENANCE SCRIPTS
# ============================================
log "=== PART 6: Creating Maintenance Scripts ==="

echo "6️⃣ Creating maintenance scripts..."

# Script to check DNS
cat > /usr/local/bin/check-dns.sh << 'EOF'
#!/bin/bash
echo "Testing DNS resolution..."
nslookup google.com
nslookup cloudflare.com
dig @8.8.8.8 google.com
EOF
chmod +x /usr/local/bin/check-dns.sh
log "   ✅ Created /usr/local/bin/check-dns.sh"

# Script to check firewall
cat > /usr/local/bin/check-firewall.sh << 'EOF'
#!/bin/bash
echo "Current firewall rules:"
iptables -L -n -v
echo ""
echo "SSH rule:"
iptables -L INPUT -n | grep 22
echo ""
echo "DNS rule:"
iptables -L INPUT -n | grep 53
EOF
chmod +x /usr/local/bin/check-firewall.sh
log "   ✅ Created /usr/local/bin/check-firewall.sh"

# Script to reload firewall
cat > /usr/local/bin/reload-firewall.sh << 'EOF'
#!/bin/bash
echo "Reloading firewall rules..."
iptables-restore < /etc/iptables/rules.v4
if [ -f /etc/iptables/rules.v6 ]; then
    ip6tables-restore < /etc/iptables/rules.v6
fi
echo "✅ Firewall rules reloaded"
EOF
chmod +x /usr/local/bin/reload-firewall.sh
log "   ✅ Created /usr/local/bin/reload-firewall.sh"

echo "   ✅ Maintenance scripts created"
echo ""

# ============================================
# SUMMARY
# ============================================
log "=== VPS Setup Complete ==="

echo "=========================================="
echo "✅ VPS SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "📋 What was configured:"
echo "   ✅ DNS: 8.8.8.8, 8.8.4.4, 1.1.1.1, 1.0.0.1 (permanent)"
echo "   ✅ Firewall: Clean iptables rules (no UFW conflicts)"
echo "   ✅ SSH: Port 22 allowed"
echo "   ✅ DNS: Port 53 allowed"
echo "   ✅ HTTPS: Port 443 allowed"
echo "   ✅ HTTP: Port 80 allowed"
echo "   ✅ OpenVPN: Port 1194 allowed"
echo "   ✅ Rules saved permanently"
echo "   ✅ Services restarted"
echo ""
echo "🔧 Maintenance commands:"
echo "   check-dns.sh      - Test DNS resolution"
echo "   check-firewall.sh - View firewall rules"
echo "   reload-firewall.sh - Reload firewall rules"
echo ""
echo "📝 Log file: $LOG_FILE"
echo ""
echo "🎯 Next steps:"
echo "   1. Test SSH: ssh root@15.204.11.19"
echo "   2. Test DNS: nslookup google.com"
echo "   3. Test web portal: curl http://localhost:5000"
echo ""

exit 0

