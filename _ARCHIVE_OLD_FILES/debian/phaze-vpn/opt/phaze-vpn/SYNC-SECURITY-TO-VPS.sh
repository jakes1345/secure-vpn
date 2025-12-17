#!/bin/bash
# Sync ALL Security Updates to VPS
# This syncs all the new security enhancements we've built

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PATH="/opt/secure-vpn"
LOCAL_PATH="/opt/phaze-vpn"

echo "=========================================="
echo "🔄 SYNCING SECURITY UPDATES TO VPS"
echo "=========================================="
echo ""
echo "VPS: ${VPS_USER}@${VPS_IP}"
echo "Remote Path: ${VPS_PATH}"
echo "Local Path: ${LOCAL_PATH}"
echo ""

# Check if we're in the right directory
if [ ! -f "${LOCAL_PATH}/config/server.conf" ]; then
    echo "❌ Error: Can't find config/server.conf"
    echo "   Make sure you're running this from the project root"
    exit 1
fi

echo "📋 Security files to sync:"
echo "  ✓ config/server.conf (VPN-native security)"
echo "  ✓ scripts/up-ultimate-security.sh (WebRTC/IPv6 routing)"
echo "  ✓ scripts/down-ultimate-security.sh (cleanup)"
echo "  ✓ scripts/setup-ddos-protection.sh (DDoS protection)"
echo "  ✓ scripts/monitor-ddos.sh (monitoring)"
echo "  ✓ scripts/enhance-privacy.sh (privacy)"
echo "  ✓ scripts/setup-vpn-ipv6.sh (IPv6 setup)"
echo "  ✓ vpn-manager.py (updated client configs)"
echo ""

# Create backup directory on VPS
echo "📦 Creating backup on VPS..."
BACKUP_DIR="${VPS_PATH}/backups/$(date +%Y%m%d-%H%M%S)"
ssh ${VPS_USER}@${VPS_IP} "mkdir -p ${BACKUP_DIR}" || true

echo ""
echo "🚀 Starting sync..."
echo ""

# Sync server config
echo "[1/8] Syncing config/server.conf..."
scp ${LOCAL_PATH}/config/server.conf ${VPS_USER}@${VPS_IP}:${BACKUP_DIR}/server.conf.backup 2>/dev/null || true
scp ${LOCAL_PATH}/config/server.conf ${VPS_USER}@${VPS_IP}:${VPS_PATH}/config/server.conf
echo "   ✓ server.conf synced"

# Sync security scripts
echo "[2/8] Syncing scripts/up-ultimate-security.sh..."
scp ${LOCAL_PATH}/scripts/up-ultimate-security.sh ${VPS_USER}@${VPS_IP}:${VPS_PATH}/scripts/up-ultimate-security.sh
ssh ${VPS_USER}@${VPS_IP} "chmod +x ${VPS_PATH}/scripts/up-ultimate-security.sh"
echo "   ✓ up-ultimate-security.sh synced"

echo "[3/8] Syncing scripts/down-ultimate-security.sh..."
scp ${LOCAL_PATH}/scripts/down-ultimate-security.sh ${VPS_USER}@${VPS_IP}:${VPS_PATH}/scripts/down-ultimate-security.sh
ssh ${VPS_USER}@${VPS_IP} "chmod +x ${VPS_PATH}/scripts/down-ultimate-security.sh"
echo "   ✓ down-ultimate-security.sh synced"

echo "[4/8] Syncing scripts/setup-ddos-protection.sh..."
scp ${LOCAL_PATH}/scripts/setup-ddos-protection.sh ${VPS_USER}@${VPS_IP}:${VPS_PATH}/scripts/setup-ddos-protection.sh
ssh ${VPS_USER}@${VPS_IP} "chmod +x ${VPS_PATH}/scripts/setup-ddos-protection.sh"
echo "   ✓ setup-ddos-protection.sh synced"

echo "[5/8] Syncing scripts/monitor-ddos.sh..."
if [ -f "${LOCAL_PATH}/scripts/monitor-ddos.sh" ]; then
    scp ${LOCAL_PATH}/scripts/monitor-ddos.sh ${VPS_USER}@${VPS_IP}:${VPS_PATH}/scripts/monitor-ddos.sh
    ssh ${VPS_USER}@${VPS_IP} "chmod +x ${VPS_PATH}/scripts/monitor-ddos.sh"
    echo "   ✓ monitor-ddos.sh synced"
else
    echo "   ⚠️  monitor-ddos.sh not found (created by setup-ddos-protection.sh)"
fi

echo "[6/8] Syncing scripts/enhance-privacy.sh..."
scp ${LOCAL_PATH}/scripts/enhance-privacy.sh ${VPS_USER}@${VPS_IP}:${VPS_PATH}/scripts/enhance-privacy.sh
ssh ${VPS_USER}@${VPS_IP} "chmod +x ${VPS_PATH}/scripts/enhance-privacy.sh"
echo "   ✓ enhance-privacy.sh synced"

echo "[7/8] Syncing scripts/setup-vpn-ipv6.sh..."
scp ${LOCAL_PATH}/scripts/setup-vpn-ipv6.sh ${VPS_USER}@${VPS_IP}:${VPS_PATH}/scripts/setup-vpn-ipv6.sh
ssh ${VPS_USER}@${VPS_IP} "chmod +x ${VPS_PATH}/scripts/setup-vpn-ipv6.sh"
echo "   ✓ setup-vpn-ipv6.sh synced"

echo "[8/8] Syncing vpn-manager.py..."
scp ${LOCAL_PATH}/vpn-manager.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/vpn-manager.py
ssh ${VPS_USER}@${VPS_IP} "chmod +x ${VPS_PATH}/vpn-manager.py"
echo "   ✓ vpn-manager.py synced"

echo ""
echo "=========================================="
echo "✅ SYNC COMPLETE!"
echo "=========================================="
echo ""
echo "📝 Next steps on VPS:"
echo ""
echo "1. SSH into VPS:"
echo "   ssh ${VPS_USER}@${VPS_IP}"
echo ""
echo "2. Setup DDoS protection:"
echo "   cd ${VPS_PATH}"
echo "   sudo ./scripts/setup-ddos-protection.sh"
echo ""
echo "3. Setup privacy enhancements:"
echo "   sudo ./scripts/enhance-privacy.sh"
echo ""
echo "4. Restart OpenVPN service:"
echo "   sudo systemctl restart openvpn@server"
echo "   # OR if using different service name:"
echo "   sudo systemctl restart secure-vpn"
echo ""
echo "5. Test VPN connection:"
echo "   # Connect from client and verify:"
echo "   # - Kill switch works"
echo "   # - DNS leak protection works"
echo "   # - WebRTC routes through VPN"
echo "   # - IPv6 routes through VPN"
echo ""
echo "6. Monitor security:"
echo "   ${VPS_PATH}/scripts/monitor-ddos.sh"
echo ""
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Test everything before going live!"
echo ""

