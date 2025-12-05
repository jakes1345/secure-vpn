#!/bin/bash
# OpenVPN Up Script for Linux
# Enables IP forwarding and NAT for VPN clients

# Get the VPN interface name (usually tun0)
VPN_DEVICE="$1"
VPN_IP="$4"
VPN_MASK="$5"

# Get the default network interface (usually eth0, enp0s3, etc.)
DEFAULT_IF=$(ip route | grep default | awk '{print $5}' | head -1)

if [ -z "$DEFAULT_IF" ]; then
    DEFAULT_IF=$(ip route | grep default | awk '{print $3}' | head -1)
    # Try to get interface from default route
    DEFAULT_IF=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $5; exit}')
fi

echo "[OpenVPN] Configuring routing for $VPN_DEVICE..."

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Make it persistent
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf 2>/dev/null; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi

# Set up NAT masquerading for VPN subnet
if [ -n "$DEFAULT_IF" ]; then
    # Check if rule already exists
    if ! iptables -t nat -C POSTROUTING -s 10.8.0.0/24 -o "$DEFAULT_IF" -j MASQUERADE 2>/dev/null; then
        iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o "$DEFAULT_IF" -j MASQUERADE
        echo "[OpenVPN] Added NAT rule for $DEFAULT_IF"
    fi
    
    # Allow forwarding from VPN to internet
    if ! iptables -C FORWARD -i "$VPN_DEVICE" -o "$DEFAULT_IF" -j ACCEPT 2>/dev/null; then
        iptables -A FORWARD -i "$VPN_DEVICE" -o "$DEFAULT_IF" -j ACCEPT
        echo "[OpenVPN] Added forward rule: $VPN_DEVICE -> $DEFAULT_IF"
    fi
    
    # Allow forwarding from internet to VPN
    if ! iptables -C FORWARD -i "$DEFAULT_IF" -o "$VPN_DEVICE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null; then
        iptables -A FORWARD -i "$DEFAULT_IF" -o "$VPN_DEVICE" -m state --state RELATED,ESTABLISHED -j ACCEPT
        echo "[OpenVPN] Added forward rule: $DEFAULT_IF -> $VPN_DEVICE"
    fi
else
    echo "[WARNING] Could not determine default network interface"
    echo "[INFO] You may need to manually configure NAT"
fi

echo "[OpenVPN] Routing configured successfully"
exit 0

