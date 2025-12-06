#!/bin/bash
# Start email worker service on VPS

VPS_IP="15.204.11.19"
VPS_USER="root"

echo "=========================================="
echo "📧 STARTING EMAIL WORKER ON VPS"
echo "=========================================="
echo ""

ssh ${VPS_USER}@${VPS_IP} << 'EOF'
    echo "[1/3] Reloading systemd..."
    systemctl daemon-reload
    echo "   ✅ Systemd reloaded"
    echo ""
    
    echo "[2/3] Enabling email-worker service..."
    systemctl enable email-worker
    echo "   ✅ Service enabled"
    echo ""
    
    echo "[3/3] Starting email-worker service..."
    systemctl start email-worker
    echo "   ✅ Service started"
    echo ""
    
    echo "Service status:"
    systemctl status email-worker --no-pager -l | head -20
EOF

echo ""
echo "✅ Done"
echo ""
echo "To check logs:"
echo "  ssh root@15.204.11.19 'journalctl -u email-worker -f'"
