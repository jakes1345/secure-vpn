#!/bin/bash
# Final Verification - Check Everything is Invisible
# Run this ON THE VPS

echo "🔒 Final Security Verification..."
echo ""

# 1. Ghost Mode Check
echo "=== 1. Ghost Mode (Zero Logging) ==="
if grep -q "^verb 0" /etc/openvpn/server.conf; then
    echo "✅ Zero logging: ENABLED"
else
    echo "❌ Zero logging: NOT ENABLED"
fi

if [ -f "/etc/openvpn/certs/dh4096.pem" ]; then
    echo "✅ 4096-bit DH: EXISTS"
    if grep -q "dh.*4096\|dh certs/dh4096" /etc/openvpn/server.conf; then
        echo "✅ 4096-bit DH: IN USE"
    else
        echo "⚠️  4096-bit DH: NOT IN USE (check config)"
    fi
else
    echo "❌ 4096-bit DH: MISSING"
fi

# 2. OpenVPN Obfuscation Check
echo ""
echo "=== 2. OpenVPN Obfuscation (Mobile) ==="
if systemctl is-active --quiet openvpn-obfsproxy 2>/dev/null; then
    echo "✅ obfsproxy: RUNNING"
    if netstat -tuln 2>/dev/null | grep -q ":443 " || ss -tuln 2>/dev/null | grep -q ":443 "; then
        echo "✅ Port 443: LISTENING"
    else
        echo "⚠️  Port 443: NOT LISTENING"
    fi
else
    echo "❌ obfsproxy: NOT RUNNING"
    echo "   Check: systemctl status openvpn-obfsproxy"
fi

# 3. PhazeVPN Protocol Check
echo ""
echo "=== 3. PhazeVPN Protocol (Desktop) ==="
PROTOCOL_DIR="/opt/phazevpn/phazevpn-protocol"
if [ -d "$PROTOCOL_DIR" ]; then
    echo "✅ PhazeVPN Protocol directory: EXISTS"
    
    if [ -f "$PROTOCOL_DIR/phazevpn-server-production.py" ]; then
        if grep -q "port=443\|port = 443" "$PROTOCOL_DIR/phazevpn-server-production.py"; then
            echo "✅ Port 443: CONFIGURED"
        else
            echo "⚠️  Port 443: NOT CONFIGURED (still using 51821)"
            echo "   Fix: sed -i 's/port=51821/port=443/g' $PROTOCOL_DIR/phazevpn-server-production.py"
        fi
        
        if grep -q "obfuscator = TrafficObfuscator(obfuscate=True)" "$PROTOCOL_DIR/phazevpn-server-production.py"; then
            echo "✅ Obfuscation: ENABLED"
        else
            echo "⚠️  Obfuscation: CHECK MANUALLY"
        fi
    else
        echo "⚠️  Server file: NOT FOUND"
    fi
    
    if systemctl is-active --quiet phazevpn-protocol 2>/dev/null; then
        echo "✅ Service: RUNNING"
    else
        echo "⚠️  Service: NOT RUNNING or NOT FOUND"
    fi
else
    echo "⚠️  PhazeVPN Protocol: DIRECTORY NOT FOUND"
    echo "   Expected: $PROTOCOL_DIR"
fi

# 4. Port Check
echo ""
echo "=== 4. Port Status ==="
echo "Listening on port 443:"
netstat -tuln 2>/dev/null | grep ":443 " || ss -tuln 2>/dev/null | grep ":443 " || echo "   No process listening on 443"

# 5. Encryption Check
echo ""
echo "=== 5. Encryption Settings ==="
grep -E "cipher|auth|tls-version" /etc/openvpn/server.conf | head -3

# 6. Summary
echo ""
echo "=== SUMMARY ==="
echo ""
GHOST_OK=$(grep -q "^verb 0" /etc/openvpn/server.conf && echo "YES" || echo "NO")
DH_OK=$([ -f "/etc/openvpn/certs/dh4096.pem" ] && echo "YES" || echo "NO")
OBFS_OK=$(systemctl is-active --quiet openvpn-obfsproxy 2>/dev/null && echo "YES" || echo "NO")
PORT443_OK=$(netstat -tuln 2>/dev/null | grep -q ":443 " && echo "YES" || echo "NO")

echo "Ghost Mode (Zero Logging): $GHOST_OK"
echo "4096-bit DH: $DH_OK"
echo "OpenVPN Obfuscation: $OBFS_OK"
echo "Port 443 Active: $PORT443_OK"
echo ""

if [ "$GHOST_OK" = "YES" ] && [ "$DH_OK" = "YES" ] && [ "$OBFS_OK" = "YES" ] && [ "$PORT443_OK" = "YES" ]; then
    echo "🎉 ALL SYSTEMS GO! You are INVISIBLE!"
else
    echo "⚠️  Some features need attention (see above)"
fi

