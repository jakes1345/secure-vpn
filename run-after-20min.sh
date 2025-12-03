#!/bin/bash
# Run automated browser build after 20 minutes
# This script waits 20 minutes then runs the automated build system

echo "=========================================="
echo "⏰ PhazeBrowser Automated Build"
echo "=========================================="
echo ""
echo "Waiting 20 minutes before checking sync status..."
echo "Started at: $(date)"
echo ""

# Wait 20 minutes (1200 seconds)
sleep 1200

echo ""
echo "20 minutes elapsed - checking status and starting build..."
echo "Time: $(date)"
echo ""

# Run the automated build system
cd "$(dirname "$0")"
python3 automated-browser-build.py

echo ""
echo "=========================================="
echo "✅ Automated build system completed"
echo "=========================================="
echo ""
echo "Check status with: python3 check-browser-status-now.py"

