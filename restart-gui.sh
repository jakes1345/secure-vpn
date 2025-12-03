#!/bin/bash
# Simple script to kill old GUI and start fresh

echo "🔄 Restarting PhazeVPN GUI..."
echo ""

# Kill any running GUI processes
echo "1. Killing old GUI processes..."
pkill -f "vpn-gui.py" 2>/dev/null
pkill -f "phazevpn-client" 2>/dev/null
sleep 1

# Clear Python cache
echo "2. Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Start fresh GUI
echo "3. Starting NEW GUI..."
echo ""
cd "$(dirname "$0")"
python3 vpn-gui.py

