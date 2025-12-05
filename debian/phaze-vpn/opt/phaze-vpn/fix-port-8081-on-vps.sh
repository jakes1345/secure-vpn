#!/bin/bash
# Run this ON THE VPS to fix port 8081 issue

echo "🔧 Fixing port 8081 issue..."

# Kill any old instances
pkill -f client-download-server.py
sleep 2

# Check if port is still in use
if lsof -i :8081 > /dev/null 2>&1; then
    echo "⚠️  Port 8081 still in use, killing processes..."
    lsof -ti :8081 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Restart service
systemctl restart phaze-vpn-download
sleep 2

# Check status
systemctl status phaze-vpn-download --no-pager

echo ""
echo "✅ Done! Check status above."

