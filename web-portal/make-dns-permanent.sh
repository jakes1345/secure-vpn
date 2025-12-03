#!/bin/bash
# Make DNS firewall rules permanent

# Save current rules
iptables-save > /etc/iptables/rules.v4

# Install iptables-persistent if not installed
if ! dpkg -l | grep -q iptables-persistent; then
    apt-get update -qq
    apt-get install -y iptables-persistent -qq
fi

# Enable netfilter-persistent
systemctl enable netfilter-persistent 2>/dev/null || systemctl enable iptables-persistent 2>/dev/null || true

echo "✅ Firewall rules saved permanently"

