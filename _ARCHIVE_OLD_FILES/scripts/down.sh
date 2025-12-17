#!/bin/bash
# OpenVPN Down Script for Linux
# Cleans up routing rules when VPN is stopped

VPN_DEVICE="$1"

echo "[OpenVPN] Cleaning up routing for $VPN_DEVICE..."

# Get the default network interface
DEFAULT_IF=$(ip route | grep default | awk '{print $5}' | head -1)

if [ -z "$DEFAULT_IF" ]; then
    DEFAULT_IF=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $5; exit}')
fi

# Remove NAT masquerading rule
if [ -n "$DEFAULT_IF" ]; then
    iptables -t nat -D POSTROUTING -s 10.8.0.0/24 -o "$DEFAULT_IF" -j MASQUERADE 2>/dev/null
    iptables -D FORWARD -i "$VPN_DEVICE" -o "$DEFAULT_IF" -j ACCEPT 2>/dev/null
    iptables -D FORWARD -i "$DEFAULT_IF" -o "$VPN_DEVICE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null
fi

echo "[OpenVPN] Routing cleanup complete"
exit 0

