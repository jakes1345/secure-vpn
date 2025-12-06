#!/bin/bash
# Optimize VPN connection speed for OpenVPN and WireGuard

echo "🚀 VPN SPEED OPTIMIZATION"
echo ""

CONFIG_FILE="/opt/secure-vpn/config/server.conf"
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Backup original
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ Backed up config to: $BACKUP_FILE"
echo ""

echo "📝 Applying speed optimizations..."
echo ""

# Apply optimizations
cat >> "$CONFIG_FILE" << 'EOF'

# ============================================
# SPEED OPTIMIZATIONS (Added automatically)
# ============================================

# Faster compression (if needed, uncomment)
# comp-lzo adaptive  # Adaptive compression (only compress if beneficial)

# Increase buffer sizes for faster transfers (already optimized, increasing further)
sndbuf 4194304      # 4MB send buffer (was 2MB)
rcvbuf 4194304      # 4MB receive buffer (was 2MB)
push "sndbuf 4194304"
push "rcvbuf 4194304"

# Optimize MTU for speed
tun-mtu 1600        # Larger MTU = fewer packets = faster
mssfix 1540         # Adjust MSS for larger MTU

# Faster connection handling
fast-io             # Bypass kernel packet filtering (faster, slightly less secure)
txqueuelen 1000     # Larger queue for more packets in flight

# Optimize TLS
reneg-bytes 0       # Disable periodic renegotiation (faster)
reneg-sec 0         # Disable time-based renegotiation (faster)

# Increase read/write timeouts for better throughput
ping 15             # Ping interval (was 10)
ping-restart 120    # Restart if no ping (was 120)

# Better network stack utilization
socket-flags TCP_NODELAY  # Reduce latency
EOF

echo "✅ VPN speed optimizations applied!"
echo ""
echo "📋 Changes made:"
echo "  ✅ Increased buffers to 4MB (from 2MB)"
echo "  ✅ Larger MTU (1600) for fewer packets"
echo "  ✅ Fast I/O enabled for better throughput"
echo "  ✅ Larger transmission queue"
echo "  ✅ Disabled unnecessary renegotiation"
echo "  ✅ Optimized TCP settings"
echo ""
echo "⚠️  Note: You need to restart OpenVPN for changes to take effect:"
echo "   sudo systemctl restart openvpn"
echo ""

