#!/bin/bash
# ============================================
# COMPLETE VPS DIAGNOSTIC
# Check firewall, DNS, SSH, network - EVERYTHING
# ============================================

echo "=========================================="
echo "🔍 COMPLETE VPS DIAGNOSTIC"
echo "=========================================="
echo ""

# ============================================
# 1. NETWORK CONNECTIVITY
# ============================================
echo "1️⃣ NETWORK CONNECTIVITY"
echo "----------------------------------------"
echo "Testing ping to VPS..."
if ping -c 2 -W 2 15.204.11.19 >/dev/null 2>&1; then
    echo "   ✅ VPS responds to ping"
else
    echo "   ❌ VPS does NOT respond to ping"
    echo "   💡 VPS might be down or network blocked"
fi

echo ""
echo "Testing port 22 (SSH)..."
if timeout 3 bash -c "echo > /dev/tcp/15.204.11.19/22" 2>/dev/null; then
    echo "   ✅ Port 22 is OPEN"
else
    echo "   ❌ Port 22 is CLOSED/BLOCKED"
    echo "   💡 Could be: VPS firewall, OVH Edge Firewall, or VPS down"
fi

echo ""
echo "Testing port 80 (HTTP)..."
if timeout 3 bash -c "echo > /dev/tcp/15.204.11.19/80" 2>/dev/null; then
    echo "   ✅ Port 80 is OPEN"
else
    echo "   ❌ Port 80 is CLOSED/BLOCKED"
fi

echo ""
echo "Testing port 443 (HTTPS)..."
if timeout 3 bash -c "echo > /dev/tcp/15.204.11.19/443" 2>/dev/null; then
    echo "   ✅ Port 443 is OPEN"
else
    echo "   ❌ Port 443 is CLOSED/BLOCKED"
fi

echo ""
echo "Testing port 1194 (OpenVPN)..."
if timeout 3 bash -c "echo > /dev/udp/15.204.11.19/1194" 2>/dev/null; then
    echo "   ✅ Port 1194 (UDP) is OPEN"
else
    echo "   ❌ Port 1194 (UDP) is CLOSED/BLOCKED"
fi
echo ""

# ============================================
# 2. OVH EDGE NETWORK FIREWALL STATUS
# ============================================
echo "2️⃣ OVH EDGE NETWORK FIREWALL"
echo "----------------------------------------"
echo "   ⚠️  This must be checked in OVH Manager:"
echo "   → Bare Metal Cloud → IP → 15.204.11.19 → Firewall tab"
echo "   → Check if firewall is enabled"
echo "   → Check if port 22 (SSH) is allowed"
echo "   → Check rule priority (SSH rule should have high priority)"
echo ""

# ============================================
# 3. VPS BOOT MODE
# ============================================
echo "3️⃣ VPS BOOT MODE"
echo "----------------------------------------"
echo "   ⚠️  This must be checked in OVH Manager:"
echo "   → Bare Metal Cloud → VPS → vps-80f05cc8 → Boot section"
echo "   → Should be: 'Normal boot' or 'Boot from hard disk'"
echo "   → Should NOT be: 'Rescue mode'"
echo ""

# ============================================
# 4. DNS RESOLUTION (From Your PC)
# ============================================
echo "4️⃣ DNS RESOLUTION (From Your PC)"
echo "----------------------------------------"
echo "Testing DNS resolution..."
if nslookup 15.204.11.19 >/dev/null 2>&1; then
    echo "   ✅ DNS resolution works"
else
    echo "   ⚠️  DNS resolution test inconclusive"
fi

echo ""
echo "Testing reverse DNS..."
REVERSE_DNS=$(dig +short -x 15.204.11.19 2>/dev/null)
if [ -n "$REVERSE_DNS" ]; then
    echo "   ✅ Reverse DNS: $REVERSE_DNS"
else
    echo "   ⚠️  No reverse DNS record"
fi
echo ""

# ============================================
# 5. TRACEROUTE (See Where Connection Fails)
# ============================================
echo "5️⃣ NETWORK PATH TO VPS"
echo "----------------------------------------"
echo "Running traceroute (first 5 hops)..."
if command -v traceroute >/dev/null 2>&1; then
    traceroute -m 5 -w 2 15.204.11.19 2>/dev/null | head -10 || echo "   ⚠️  Traceroute failed or timed out"
else
    echo "   ⚠️  traceroute not installed"
fi
echo ""

# ============================================
# 6. SUMMARY & RECOMMENDATIONS
# ============================================
echo "=========================================="
echo "📋 DIAGNOSTIC SUMMARY"
echo "=========================================="
echo ""

ISSUES=0

# Check ping
if ! ping -c 1 -W 2 15.204.11.19 >/dev/null 2>&1; then
    echo "❌ ISSUE: VPS not responding to ping"
    echo "   → VPS might be down"
    echo "   → Network might be blocked"
    ISSUES=$((ISSUES + 1))
fi

# Check SSH port
if ! timeout 3 bash -c "echo > /dev/tcp/15.204.11.19/22" 2>/dev/null; then
    echo "❌ ISSUE: Port 22 (SSH) is blocked"
    echo "   → Check OVH Edge Network Firewall"
    echo "   → Check VPS internal firewall (if we can SSH)"
    echo "   → Check if VPS is in rescue mode"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "✅ Network connectivity looks good!"
    echo "   If SSH still doesn't work, check:"
    echo "   → OVH Edge Network Firewall rules"
    echo "   → VPS boot mode (should be normal boot)"
else
    echo ""
    echo "🔧 RECOMMENDED ACTIONS:"
    echo ""
    echo "1. Check OVH Manager:"
    echo "   → VPS status (is it running?)"
    echo "   → Boot mode (normal boot or rescue?)"
    echo "   → Edge Network Firewall (is port 22 allowed?)"
    echo ""
    echo "2. If VPS is in rescue mode:"
    echo "   → Change to normal boot"
    echo "   → Reboot"
    echo "   → Wait 3-5 minutes"
    echo ""
    echo "3. If Edge Network Firewall is blocking:"
    echo "   → Add rule: TCP port 22, Authorize, Priority 1"
    echo "   → Save and wait 1-2 minutes"
    echo ""
    echo "4. If VPS is down:"
    echo "   → Start it in OVH Manager"
    echo "   → Wait for it to boot"
fi

echo ""
echo "=========================================="
echo "✅ DIAGNOSTIC COMPLETE"
echo "=========================================="
echo ""
echo "Next: Check OVH Manager for:"
echo "   1. VPS status (running/stopped)"
echo "   2. Boot mode (normal/rescue)"
echo "   3. Edge Network Firewall (enabled/disabled, rules)"
echo ""

