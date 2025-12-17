#!/bin/bash
# ============================================
# COMPREHENSIVE DIAGNOSTIC SCRIPT FOR RESCUE MODE
# Run this in chroot to see EXACTLY what's wrong
# ============================================

echo "=========================================="
echo "🔍 COMPREHENSIVE VPS DIAGNOSTIC"
echo "=========================================="
echo ""

# Set PATH for chroot
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# ============================================
# 1. CHECK IF WE'RE IN CHROOT
# ============================================
echo "1️⃣ CHECKING ENVIRONMENT"
echo "----------------------------------------"
if [ -f /etc/debian_version ]; then
    echo "   ✅ In chroot (Debian system detected)"
    cat /etc/debian_version
else
    echo "   ⚠️  Not in chroot or system not detected"
fi
echo ""

# ============================================
# 2. CHECK IPTABLES RULES
# ============================================
echo "2️⃣ CURRENT IPTABLES RULES"
echo "----------------------------------------"
if command -v /sbin/iptables >/dev/null 2>&1; then
    echo "   INPUT Chain:"
    /sbin/iptables -L INPUT -n -v --line-numbers 2>/dev/null || echo "   ❌ Cannot list INPUT rules"
    echo ""
    echo "   Checking for SSH rule (port 22):"
    /sbin/iptables -L INPUT -n | grep -E "22|ssh" && echo "   ✅ SSH rule EXISTS" || echo "   ❌ SSH rule MISSING!"
    echo ""
    echo "   Default Policies:"
    /sbin/iptables -L -n | grep "Chain" | head -3
else
    echo "   ❌ iptables command not found!"
fi
echo ""

# ============================================
# 3. CHECK UFW STATUS
# ============================================
echo "3️⃣ UFW STATUS"
echo "----------------------------------------"
if [ -f /etc/ufw/ufw.conf ]; then
    echo "   UFW Config File:"
    cat /etc/ufw/ufw.conf
    echo ""
    if grep -q "ENABLED=no" /etc/ufw/ufw.conf; then
        echo "   ✅ UFW is DISABLED in config"
    else
        echo "   ❌ UFW is ENABLED in config (this could block SSH!)"
    fi
else
    echo "   ⚠️  UFW config file not found"
fi

if [ -f /etc/default/ufw ]; then
    echo "   UFW Default Config:"
    cat /etc/default/ufw
fi
echo ""

# ============================================
# 4. CHECK SSH SERVICE
# ============================================
echo "4️⃣ SSH SERVICE STATUS"
echo "----------------------------------------"
if [ -f /etc/ssh/sshd_config ]; then
    echo "   ✅ SSH config file exists"
    echo "   SSH Port:"
    grep "^Port" /etc/ssh/sshd_config || grep "^#Port" /etc/ssh/sshd_config || echo "   Using default port 22"
    echo "   PermitRootLogin:"
    grep "^PermitRootLogin" /etc/ssh/sshd_config || grep "^#PermitRootLogin" /etc/ssh/sshd_config || echo "   Using default (yes)"
    echo "   PasswordAuthentication:"
    grep "^PasswordAuthentication" /etc/ssh/sshd_config || grep "^#PasswordAuthentication" /etc/ssh/sshd_config || echo "   Using default (yes)"
else
    echo "   ❌ SSH config file NOT FOUND!"
fi

# Check if SSH service files exist
if [ -f /lib/systemd/system/ssh.service ] || [ -f /lib/systemd/system/sshd.service ]; then
    echo "   ✅ SSH service file exists"
else
    echo "   ❌ SSH service file NOT FOUND!"
fi

# Check if SSH is enabled (symlink exists)
if [ -L /etc/systemd/system/multi-user.target.wants/ssh.service ] || [ -L /etc/systemd/system/multi-user.target.wants/sshd.service ]; then
    echo "   ✅ SSH service is ENABLED (symlink exists)"
else
    echo "   ❌ SSH service is NOT ENABLED (no symlink)"
fi
echo ""

# ============================================
# 5. CHECK DNS CONFIGURATION
# ============================================
echo "5️⃣ DNS CONFIGURATION"
echo "----------------------------------------"
if [ -f /etc/resolv.conf ]; then
    echo "   /etc/resolv.conf:"
    cat /etc/resolv.conf
    if grep -q "8.8.8.8\|8.8.4.4\|1.1.1.1" /etc/resolv.conf; then
        echo "   ✅ DNS servers configured"
    else
        echo "   ⚠️  DNS servers may not be configured correctly"
    fi
else
    echo "   ❌ /etc/resolv.conf NOT FOUND!"
fi
echo ""

# ============================================
# 6. CHECK BOOT SCRIPTS
# ============================================
echo "6️⃣ BOOT SCRIPTS (Firewall Rules on Boot)"
echo "----------------------------------------"
echo "   Network Script:"
if [ -f /etc/network/if-pre-up.d/iptables-load ]; then
    echo "   ✅ /etc/network/if-pre-up.d/iptables-load EXISTS"
    echo "   Content:"
    head -5 /etc/network/if-pre-up.d/iptables-load
else
    echo "   ❌ Network script MISSING"
fi
echo ""

echo "   rc.local:"
if [ -f /etc/rc.local ]; then
    echo "   ✅ /etc/rc.local EXISTS"
    if [ -x /etc/rc.local ]; then
        echo "   ✅ rc.local is EXECUTABLE"
    else
        echo "   ❌ rc.local is NOT EXECUTABLE"
    fi
    echo "   Content:"
    head -10 /etc/rc.local
else
    echo "   ❌ rc.local MISSING"
fi
echo ""

echo "   Systemd Service:"
if [ -f /etc/systemd/system/ssh-firewall-fix.service ]; then
    echo "   ✅ ssh-firewall-fix.service EXISTS"
    if [ -L /etc/systemd/system/multi-user.target.wants/ssh-firewall-fix.service ]; then
        echo "   ✅ Service is ENABLED"
    else
        echo "   ⚠️  Service exists but not enabled"
    fi
else
    echo "   ❌ ssh-firewall-fix.service MISSING"
fi
echo ""

# ============================================
# 7. CHECK IPTABLES RULES FILE
# ============================================
echo "7️⃣ IPTABLES RULES FILE (Persistent Rules)"
echo "----------------------------------------"
if [ -f /etc/iptables/rules.v4 ]; then
    echo "   ✅ Rules file EXISTS"
    echo "   File size: $(wc -l < /etc/iptables/rules.v4) lines"
    echo "   Checking for SSH rule in file:"
    if grep -q "22\|ssh" /etc/iptables/rules.v4; then
        echo "   ✅ SSH rule found in rules file"
        grep -E "22|ssh" /etc/iptables/rules.v4 | head -3
    else
        echo "   ❌ SSH rule NOT in rules file!"
    fi
else
    echo "   ❌ Rules file MISSING - rules won't persist on boot!"
fi
echo ""

# ============================================
# 8. CHECK NETWORK INTERFACES
# ============================================
echo "8️⃣ NETWORK INTERFACES"
echo "----------------------------------------"
if command -v /sbin/ip >/dev/null 2>&1; then
    /sbin/ip addr show 2>/dev/null | head -20 || echo "   ⚠️  Cannot list interfaces"
elif command -v /sbin/ifconfig >/dev/null 2>&1; then
    /sbin/ifconfig 2>/dev/null | head -20 || echo "   ⚠️  Cannot list interfaces"
else
    echo "   ⚠️  Network tools not available"
fi
echo ""

# ============================================
# 9. CHECK SYSTEM LOGS (if accessible)
# ============================================
echo "9️⃣ SYSTEM LOGS (Recent SSH/Firewall Errors)"
echo "----------------------------------------"
if [ -d /var/log ]; then
    echo "   Checking for recent errors..."
    if [ -f /var/log/syslog ]; then
        echo "   Last 10 lines of syslog:"
        tail -10 /var/log/syslog 2>/dev/null | grep -E "ssh|firewall|iptables|ufw" || echo "   No recent SSH/firewall entries"
    fi
    if [ -f /var/log/auth.log ]; then
        echo "   Last 5 lines of auth.log:"
        tail -5 /var/log/auth.log 2>/dev/null || echo "   Cannot read auth.log"
    fi
else
    echo "   ⚠️  Log directory not accessible in chroot"
fi
echo ""

# ============================================
# 10. SUMMARY & RECOMMENDATIONS
# ============================================
echo "=========================================="
echo "📋 DIAGNOSTIC SUMMARY"
echo "=========================================="
echo ""

# Count issues
ISSUES=0

# Check SSH rule
if ! /sbin/iptables -L INPUT -n 2>/dev/null | grep -q "22\|ssh"; then
    echo "❌ ISSUE: SSH rule (port 22) NOT in iptables"
    ISSUES=$((ISSUES + 1))
fi

# Check UFW
if [ -f /etc/ufw/ufw.conf ] && ! grep -q "ENABLED=no" /etc/ufw/ufw.conf; then
    echo "❌ ISSUE: UFW is ENABLED (will conflict with iptables)"
    ISSUES=$((ISSUES + 1))
fi

# Check rules file
if [ ! -f /etc/iptables/rules.v4 ]; then
    echo "❌ ISSUE: Rules file missing (rules won't persist on boot)"
    ISSUES=$((ISSUES + 1))
fi

# Check SSH service
if [ ! -L /etc/systemd/system/multi-user.target.wants/ssh.service ] && [ ! -L /etc/systemd/system/multi-user.target.wants/sshd.service ]; then
    echo "❌ ISSUE: SSH service not enabled on boot"
    ISSUES=$((ISSUES + 1))
fi

# Check boot scripts
if [ ! -f /etc/network/if-pre-up.d/iptables-load ] && [ ! -f /etc/rc.local ]; then
    echo "❌ ISSUE: No boot scripts to load firewall rules"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "✅ No obvious issues found in configuration"
    echo ""
    echo "If SSH still doesn't work after reboot:"
    echo "   1. Check OVH Edge Network Firewall in OVH Manager"
    echo "      → Bare Metal Cloud → IP → 15.204.11.19 → Firewall tab"
    echo "   2. Check DDoS mitigation status"
    echo "      → Network → Network Security Dashboard"
    echo "   3. Contact OVH support"
else
    echo "❌ Found $ISSUES issue(s) that need fixing"
    echo ""
    echo "=========================================="
    echo "🔧 HOW TO FIX EACH ISSUE"
    echo "=========================================="
    echo ""
    
    # Check SSH rule
    if ! /sbin/iptables -L INPUT -n 2>/dev/null | grep -q "22\|ssh"; then
        echo "❌ ISSUE 1: SSH rule (port 22) NOT in iptables"
        echo "   FIX: /sbin/iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT"
        echo ""
    fi
    
    # Check UFW
    if [ -f /etc/ufw/ufw.conf ] && ! grep -q "ENABLED=no" /etc/ufw/ufw.conf; then
        echo "❌ ISSUE 2: UFW is ENABLED (will conflict with iptables)"
        echo "   FIX: /bin/echo 'ENABLED=no' > /etc/ufw/ufw.conf"
        echo "   FIX: /bin/echo 'ENABLED=no' > /etc/default/ufw"
        echo ""
    fi
    
    # Check rules file
    if [ ! -f /etc/iptables/rules.v4 ]; then
        echo "❌ ISSUE 3: Rules file missing (rules won't persist on boot)"
        echo "   FIX: /bin/mkdir -p /etc/iptables"
        echo "   FIX: /sbin/iptables-save > /etc/iptables/rules.v4"
        echo ""
    fi
    
    # Check SSH service
    if [ ! -L /etc/systemd/system/multi-user.target.wants/ssh.service ] && [ ! -L /etc/systemd/system/multi-user.target.wants/sshd.service ]; then
        echo "❌ ISSUE 4: SSH service not enabled on boot"
        echo "   FIX: /bin/ln -sf /lib/systemd/system/ssh.service /etc/systemd/system/multi-user.target.wants/ssh.service"
        echo "   OR: /bin/ln -sf /lib/systemd/system/sshd.service /etc/systemd/system/multi-user.target.wants/sshd.service"
        echo ""
    fi
    
    # Check boot scripts
    if [ ! -f /etc/network/if-pre-up.d/iptables-load ] && [ ! -f /etc/rc.local ]; then
        echo "❌ ISSUE 5: No boot scripts to load firewall rules"
        echo "   FIX: Create /etc/network/if-pre-up.d/iptables-load"
        echo "   FIX: Create /etc/rc.local"
        echo ""
    fi
    
    echo "=========================================="
    echo "💡 EASIEST FIX: Run ALL commands from CHROOT-FINAL-FIX.txt"
    echo "   This will fix ALL issues at once"
    echo "=========================================="
fi

echo ""
echo "=========================================="
echo "✅ DIAGNOSTIC COMPLETE"
echo "=========================================="

