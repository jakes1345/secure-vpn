#!/bin/bash
# ============================================
# DIAGNOSE AND AUTO-FIX ISSUES
# This will show what's wrong AND fix it automatically
# ============================================

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

echo "=========================================="
echo "🔍 DIAGNOSING AND FIXING VPS ISSUES"
echo "=========================================="
echo ""

FIXES_APPLIED=0

# ============================================
# 1. CHECK AND FIX IPTABLES SSH RULE
# ============================================
echo "1️⃣ Checking SSH rule in iptables..."
if ! /sbin/iptables -L INPUT -n 2>/dev/null | grep -q "22\|ssh"; then
    echo "   ❌ SSH rule MISSING - Adding it now..."
    /sbin/iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT 2>/dev/null
    if /sbin/iptables -L INPUT -n | grep -q "22\|ssh"; then
        echo "   ✅ SSH rule ADDED"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    else
        echo "   ❌ Failed to add SSH rule"
    fi
else
    echo "   ✅ SSH rule EXISTS"
fi
echo ""

# ============================================
# 2. CHECK AND FIX UFW
# ============================================
echo "2️⃣ Checking UFW status..."
if [ -f /etc/ufw/ufw.conf ]; then
    if ! grep -q "ENABLED=no" /etc/ufw/ufw.conf; then
        echo "   ❌ UFW is ENABLED - Disabling it now..."
        /bin/echo 'ENABLED=no' > /etc/ufw/ufw.conf
        /bin/echo 'ENABLED=no' > /etc/default/ufw 2>/dev/null || true
        if grep -q "ENABLED=no" /etc/ufw/ufw.conf; then
            echo "   ✅ UFW DISABLED"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        else
            echo "   ❌ Failed to disable UFW"
        fi
    else
        echo "   ✅ UFW is already DISABLED"
    fi
else
    echo "   ⚠️  UFW config not found (might not be installed)"
fi
echo ""

# ============================================
# 3. CHECK AND FIX RULES FILE
# ============================================
echo "3️⃣ Checking rules file..."
if [ ! -f /etc/iptables/rules.v4 ]; then
    echo "   ❌ Rules file MISSING - Creating it now..."
    /bin/mkdir -p /etc/iptables
    /sbin/iptables-save > /etc/iptables/rules.v4 2>/dev/null
    if [ -f /etc/iptables/rules.v4 ]; then
        echo "   ✅ Rules file CREATED"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    else
        echo "   ❌ Failed to create rules file"
    fi
else
    echo "   ✅ Rules file EXISTS"
    # Update it with current rules
    /sbin/iptables-save > /etc/iptables/rules.v4 2>/dev/null
    echo "   ✅ Rules file UPDATED with current rules"
fi
echo ""

# ============================================
# 4. CHECK AND FIX SSH SERVICE
# ============================================
echo "4️⃣ Checking SSH service..."
if [ ! -L /etc/systemd/system/multi-user.target.wants/ssh.service ] && [ ! -L /etc/systemd/system/multi-user.target.wants/sshd.service ]; then
    echo "   ❌ SSH service NOT ENABLED - Enabling it now..."
    if [ -f /lib/systemd/system/ssh.service ]; then
        /bin/ln -sf /lib/systemd/system/ssh.service /etc/systemd/system/multi-user.target.wants/ssh.service 2>/dev/null
    elif [ -f /lib/systemd/system/sshd.service ]; then
        /bin/ln -sf /lib/systemd/system/sshd.service /etc/systemd/system/multi-user.target.wants/sshd.service 2>/dev/null
    fi
    if [ -L /etc/systemd/system/multi-user.target.wants/ssh.service ] || [ -L /etc/systemd/system/multi-user.target.wants/sshd.service ]; then
        echo "   ✅ SSH service ENABLED"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    else
        echo "   ❌ Failed to enable SSH service"
    fi
else
    echo "   ✅ SSH service is ENABLED"
fi
echo ""

# ============================================
# 5. CHECK AND FIX BOOT SCRIPTS
# ============================================
echo "5️⃣ Checking boot scripts..."

# Network script
if [ ! -f /etc/network/if-pre-up.d/iptables-load ]; then
    echo "   ❌ Network script MISSING - Creating it now..."
    /bin/cat > /etc/network/if-pre-up.d/iptables-load << 'EOF'
#!/bin/sh
/sbin/iptables-restore < /etc/iptables/rules.v4 2>/dev/null
/sbin/iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT 2>/dev/null
exit 0
EOF
    /bin/chmod +x /etc/network/if-pre-up.d/iptables-load
    if [ -f /etc/network/if-pre-up.d/iptables-load ]; then
        echo "   ✅ Network script CREATED"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    else
        echo "   ❌ Failed to create network script"
    fi
else
    echo "   ✅ Network script EXISTS"
fi

# rc.local
if [ ! -f /etc/rc.local ]; then
    echo "   ❌ rc.local MISSING - Creating it now..."
    /bin/cat > /etc/rc.local << 'EOF'
#!/bin/bash
/bin/sleep 3
/sbin/iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT 2>/dev/null
/sbin/iptables-save > /etc/iptables/rules.v4 2>/dev/null
exit 0
EOF
    /bin/chmod +x /etc/rc.local
    if [ -f /etc/rc.local ]; then
        echo "   ✅ rc.local CREATED"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    else
        echo "   ❌ Failed to create rc.local"
    fi
else
    echo "   ✅ rc.local EXISTS"
    if [ ! -x /etc/rc.local ]; then
        /bin/chmod +x /etc/rc.local
        echo "   ✅ rc.local made executable"
    fi
fi
echo ""

# ============================================
# 6. CHECK AND FIX DNS
# ============================================
echo "6️⃣ Checking DNS configuration..."
if [ ! -f /etc/resolv.conf ] || ! grep -q "8.8.8.8\|8.8.4.4\|1.1.1.1" /etc/resolv.conf; then
    echo "   ❌ DNS not configured - Fixing it now..."
    /bin/rm -f /etc/resolv.conf
    /bin/cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF
    if grep -q "8.8.8.8" /etc/resolv.conf; then
        echo "   ✅ DNS CONFIGURED"
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    else
        echo "   ❌ Failed to configure DNS"
    fi
else
    echo "   ✅ DNS already configured"
fi
echo ""

# ============================================
# FINAL SUMMARY
# ============================================
echo "=========================================="
echo "📋 SUMMARY"
echo "=========================================="
echo ""
echo "✅ Applied $FIXES_APPLIED fix(es)"
echo ""

# Verify everything
echo "Verifying fixes..."
VERIFIED=0

if /sbin/iptables -L INPUT -n 2>/dev/null | grep -q "22\|ssh"; then
    echo "   ✅ SSH rule in iptables"
    VERIFIED=$((VERIFIED + 1))
else
    echo "   ❌ SSH rule still missing"
fi

if [ -f /etc/ufw/ufw.conf ] && grep -q "ENABLED=no" /etc/ufw/ufw.conf; then
    echo "   ✅ UFW disabled"
    VERIFIED=$((VERIFIED + 1))
fi

if [ -f /etc/iptables/rules.v4 ]; then
    echo "   ✅ Rules file exists"
    VERIFIED=$((VERIFIED + 1))
fi

if [ -L /etc/systemd/system/multi-user.target.wants/ssh.service ] || [ -L /etc/systemd/system/multi-user.target.wants/sshd.service ]; then
    echo "   ✅ SSH service enabled"
    VERIFIED=$((VERIFIED + 1))
fi

if [ -f /etc/network/if-pre-up.d/iptables-load ] && [ -f /etc/rc.local ]; then
    echo "   ✅ Boot scripts exist"
    VERIFIED=$((VERIFIED + 1))
fi

echo ""
echo "=========================================="
if [ $VERIFIED -ge 4 ]; then
    echo "✅ ALL CRITICAL FIXES APPLIED"
    echo ""
    echo "Next steps:"
    echo "   1. Exit chroot: exit"
    echo "   2. Reboot: reboot -f"
    echo "   3. Wait 3 minutes"
    echo "   4. Test SSH: ssh root@15.204.11.19"
    echo ""
    echo "If SSH still doesn't work, check OVH Edge Network Firewall"
    echo "   → Bare Metal Cloud → IP → 15.204.11.19 → Firewall tab"
else
    echo "⚠️  Some fixes may not have applied correctly"
    echo "   Run CHROOT-FINAL-FIX.txt manually for complete fix"
fi
echo "=========================================="

