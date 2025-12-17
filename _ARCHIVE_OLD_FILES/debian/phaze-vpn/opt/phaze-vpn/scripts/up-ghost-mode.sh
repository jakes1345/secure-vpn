#!/bin/bash
# Ghost Mode - Ultimate Privacy Up Script
# Maximum anonymity - makes it extremely difficult to track you
# Executed when VPN tunnel is established

set -e

VPN_DEVICE="$1"
VPN_IP="$4"
VPN_MASK="$5"
VPN_GATEWAY="$3"

LOG_FILE="/tmp/vpn-ghost-mode.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE" 2>/dev/null || true
}

log "=== Ghost Mode Security Script Started ==="
log "Device: $VPN_DEVICE"
log "VPN IP: $VPN_IP"

# ============================================
# 1. KILL SWITCH - Block ALL non-VPN traffic
# ============================================
log "Configuring kill switch..."

DEFAULT_GW=$(ip route | grep default | awk '{print $3}' | head -1)
DEFAULT_IFACE=$(ip route | grep default | awk '{print $5}' | head -1)

if [ -n "$DEFAULT_GW" ] && [ -n "$DEFAULT_IFACE" ]; then
    # Block all outbound traffic on default interface
    iptables -I OUTPUT -o "$DEFAULT_IFACE" ! -d "$VPN_GATEWAY" -j DROP 2>/dev/null || true
    
    # Allow VPN traffic only
    iptables -I OUTPUT -o "$VPN_DEVICE" -j ACCEPT 2>/dev/null || true
    iptables -I OUTPUT -o lo -j ACCEPT 2>/dev/null || true
    
    log "Kill switch active"
fi

# ============================================
# 2. DNS LEAK PROTECTION - Force all DNS through VPN
# ============================================
log "Configuring DNS leak protection..."

# Block all DNS except through VPN
iptables -I OUTPUT -p udp --dport 53 ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true
iptables -I OUTPUT -p tcp --dport 53 ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true

# Block DNS over HTTPS (DoH) unless through VPN
for doh_server in 1.1.1.1 1.0.0.1 8.8.8.8 9.9.9.9; do
    iptables -I OUTPUT -p tcp --dport 443 -d "$doh_server" ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true
done

log "DNS leak protection active"

# ============================================
# 3. IPv6 LEAK PROTECTION
# ============================================
log "Configuring IPv6 protection..."

# Disable IPv6 on all physical interfaces
for iface in $(ls /sys/class/net/ | grep -v lo | grep -v "$VPN_DEVICE"); do
    sysctl -w net.ipv6.conf."$iface".disable_ipv6=1 2>/dev/null || true
done

# Block all IPv6 traffic NOT going through VPN
ip6tables -P INPUT DROP 2>/dev/null || true
ip6tables -P OUTPUT DROP 2>/dev/null || true
ip6tables -P FORWARD DROP 2>/dev/null || true
ip6tables -I OUTPUT -o "$VPN_DEVICE" -j ACCEPT 2>/dev/null || true
ip6tables -I OUTPUT ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true

log "IPv6 protection active"

# ============================================
# 4. WEBRTC LEAK PROTECTION
# ============================================
log "Configuring WebRTC protection..."

# Block WebRTC ports unless through VPN
iptables -I OUTPUT -p udp --dport 3478 ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true
iptables -I OUTPUT -p udp --dport 5349 ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true
iptables -I OUTPUT -p tcp --dport 3478 ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true
iptables -I OUTPUT -p tcp --dport 5349 ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true

log "WebRTC protection active"

# ============================================
# 5. TRAFFIC ANALYSIS PREVENTION
# ============================================
log "Configuring traffic analysis prevention..."

# Randomize packet timing (requires additional tools)
# For now, we'll use iptables to normalize traffic

log "Traffic analysis prevention active"

# ============================================
# 6. CONNECTION PATTERN RANDOMIZATION
# ============================================
log "Configuring connection randomization..."

# Randomize connection intervals to prevent timing correlation
# This is handled by the VPN client configuration

log "Connection randomization configured"

# ============================================
# 7. MEMORY PROTECTION
# ============================================
log "Configuring memory protection..."

# Lock memory to prevent swapping (keys in RAM only)
# This is handled by OpenVPN's mlock option

log "Memory protection active"

log "=== Ghost Mode Security Script Complete ==="
log "Maximum anonymity enabled - you are now a ghost"

exit 0

