#!/bin/bash
# Connect to PhazeVPN VPS via RDP

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"

# Check if xfreerdp is installed
if ! command -v xfreerdp &> /dev/null; then
    echo "Installing xfreerdp..."
    sudo apt-get update
    sudo apt-get install -y freerdp2-x11
fi

echo "Connecting to VPS..."
xfreerdp /v:${VPS_IP}:3389 /u:${VPS_USER} /p:${VPS_PASS} /size:1920x1080 /clipboard /compression /bpp:32
