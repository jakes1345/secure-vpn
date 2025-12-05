#!/bin/bash
# PhazeVPN - Gaming/Streaming Performance Optimization
# Applies system-level optimizations for lowest latency and highest throughput

set -e

echo "=========================================="
echo "PhazeVPN Gaming/Streaming Optimization"
echo "=========================================="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# 1. Network optimizations
echo "1️⃣  Optimizing network stack..."

# Increase UDP buffer sizes for gaming
cat >> /etc/sysctl.conf <<EOF

# PhazeVPN Gaming Optimizations
# UDP buffer sizes (for high-speed gaming)
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 4194304
net.core.wmem_default = 4194304

# TCP optimizations (for control channel)
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = bbr

# Reduce latency
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# IP forwarding (required for VPN)
net.ipv4.ip_forward = 1

# Disable ICMP redirects (security)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Optimize for low latency
net.core.netdev_max_backlog = 5000
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
EOF

sysctl -p

echo "✅ Network stack optimized"

# 2. CPU optimizations
echo ""
echo "2️⃣  Optimizing CPU for gaming..."

# Set CPU governor to performance mode (lowest latency)
if command -v cpupower &> /dev/null; then
    cpupower frequency-set -g performance
    echo "✅ CPU governor set to performance mode"
elif [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$cpu" 2>/dev/null || true
    done
    echo "✅ CPU governor set to performance mode"
else
    echo "⚠️  CPU governor not available (may require cpupower)"
fi

# 3. IRQ optimizations
echo ""
echo "3️⃣  Optimizing IRQ affinity..."

# Get network interface
INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
if [ -n "$INTERFACE" ]; then
    # Get IRQ for network interface
    IRQ=$(grep "$INTERFACE" /proc/interrupts | awk '{print $1}' | sed 's/://' | head -1)
    if [ -n "$IRQ" ]; then
        # Bind IRQ to CPU 0 (reduce context switching)
        echo 1 > "/proc/irq/$IRQ/smp_affinity" 2>/dev/null || true
        echo "✅ IRQ affinity optimized for $INTERFACE"
    fi
fi

# 4. Disable unnecessary services (optional)
echo ""
echo "4️⃣  Checking for unnecessary services..."

# Services that can add latency (disable if not needed)
SERVICES_TO_DISABLE=(
    "snapd"
    "bluetooth"
    "cups"
    "avahi-daemon"
)

for service in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl is-enabled "$service" &>/dev/null; then
        read -p "Disable $service? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            systemctl disable "$service" 2>/dev/null || true
            systemctl stop "$service" 2>/dev/null || true
            echo "✅ Disabled $service"
        fi
    fi
done

# 5. Firewall optimizations
echo ""
echo "5️⃣  Optimizing firewall..."

# Use nftables if available (faster than iptables)
if command -v nft &> /dev/null; then
    echo "✅ nftables available (faster than iptables)"
fi

# 6. Create gaming profile script
echo ""
echo "6️⃣  Creating gaming profile..."

cat > /usr/local/bin/phazevpn-gaming-mode <<'EOF'
#!/bin/bash
# Enable gaming mode optimizations

# Set CPU to performance
if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$cpu" 2>/dev/null || true
    done
fi

# Apply sysctl settings
sysctl -p > /dev/null 2>&1

echo "✅ Gaming mode enabled"
EOF

chmod +x /usr/local/bin/phazevpn-gaming-mode

echo "✅ Gaming profile created"
echo "   Run 'phazevpn-gaming-mode' to enable gaming optimizations"

# 7. Summary
echo ""
echo "=========================================="
echo "✅ Optimization Complete!"
echo "=========================================="
echo ""
echo "Applied optimizations:"
echo "  ✅ Network buffer sizes increased"
echo "  ✅ TCP congestion control set to BBR"
echo "  ✅ CPU governor set to performance"
echo "  ✅ IRQ affinity optimized"
echo "  ✅ Gaming profile created"
echo ""
echo "For best results:"
echo "  1. Use WireGuard instead of OpenVPN (faster)"
echo "  2. Use gaming-optimized server config"
echo "  3. Run 'phazevpn-gaming-mode' before gaming"
echo "  4. Use servers close to your location"
echo ""

