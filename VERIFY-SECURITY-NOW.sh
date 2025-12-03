#!/bin/bash
# Security Verification Script
# Run this to check if your VPN is actually secure

echo "🔒 Verifying VPN Security..."
echo ""

# Check if running on VPS or local
if [ -f "/etc/openvpn/server.conf" ] || [ -f "/opt/phaze-vpn/config/server.conf" ]; then
    echo "📍 Running on VPS - Checking server security..."
    ON_VPS=true
else
    echo "📍 Running on local PC - Checking client security..."
    ON_VPS=false
fi

if [ "$ON_VPS" = true ]; then
    # VPS Security Checks
    CONFIG=""
    if [ -f "/etc/openvpn/server.conf" ]; then
        CONFIG="/etc/openvpn/server.conf"
    elif [ -f "/opt/phaze-vpn/config/server.conf" ]; then
        CONFIG="/opt/phaze-vpn/config/server.conf"
    fi
    
    if [ -n "$CONFIG" ]; then
        echo ""
        echo "=== Zero Logging Check ==="
        VERB=$(grep "^verb" "$CONFIG" | awk '{print $2}')
        STATUS=$(grep "^status" "$CONFIG")
        LOG=$(grep "^log-append" "$CONFIG")
        
        if [ "$VERB" = "0" ]; then
            echo "✅ Zero logging enabled (verb 0)"
        else
            echo "❌ Logging enabled (verb $VERB) - NOT SECURE!"
        fi
        
        if [ -z "$STATUS" ] && [ -z "$LOG" ]; then
            echo "✅ Status logs disabled"
        else
            echo "⚠️  Status/logging still enabled - check manually"
        fi
        
        echo ""
        echo "=== 4096-bit DH Check ==="
        DH_FILE=$(grep "^dh " "$CONFIG" | awk '{print $2}')
        if echo "$DH_FILE" | grep -q "4096"; then
            echo "✅ Using 4096-bit DH: $DH_FILE"
            if [ -f "$DH_FILE" ]; then
                echo "✅ DH file exists"
            else
                echo "❌ DH file missing!"
            fi
        else
            echo "⚠️  Not using 4096-bit DH: $DH_FILE"
        fi
        
        echo ""
        echo "=== Encryption Check ==="
        CIPHER=$(grep -E "^cipher|^data-ciphers" "$CONFIG" | head -1)
        if echo "$CIPHER" | grep -qi "chacha\|aes-256"; then
            echo "✅ Strong encryption: $CIPHER"
        else
            echo "⚠️  Check encryption settings"
        fi
        
        TLS=$(grep "tls-version-min" "$CONFIG")
        if echo "$TLS" | grep -q "1.3"; then
            echo "✅ TLS 1.3 minimum"
        else
            echo "⚠️  Check TLS version"
        fi
        
        echo ""
        echo "=== Server Location ==="
        SERVER_IP=$(curl -s https://api.ipify.org)
        COUNTRY=$(curl -s "https://ipapi.co/$SERVER_IP/json/" | grep -o '"country_name":"[^"]*"' | cut -d'"' -f4)
        echo "Server IP: $SERVER_IP"
        echo "Country: $COUNTRY"
        
        case "$COUNTRY" in
            "Switzerland"|"Romania"|"Iceland"|"Panama")
                echo "✅ Privacy-friendly jurisdiction"
                ;;
            "United States"|"United Kingdom"|"Canada"|"Australia"|"New Zealand")
                echo "⚠️  Five Eyes jurisdiction - higher risk"
                ;;
            *)
                echo "⚠️  Check privacy laws for this country"
                ;;
        esac
        
        echo ""
        echo "=== VPN Service Status ==="
        if systemctl is-active --quiet openvpn@server 2>/dev/null; then
            echo "✅ VPN server is running"
        else
            echo "❌ VPN server not running!"
        fi
    fi
else
    # Local Client Checks
    echo ""
    echo "=== IP Leak Check ==="
    YOUR_IP=$(curl -s https://api.ipify.org)
    echo "Your current IP: $YOUR_IP"
    echo "If connected to VPN, this should be your VPN server IP"
    
    echo ""
    echo "=== DNS Leak Check ==="
    echo "Run: curl https://www.dnsleaktest.com/"
    echo "Or visit: https://dnsleaktest.com"
    echo "Should show only VPN DNS (Quad9: 9.9.9.9), not your ISP"
    
    echo ""
    echo "=== Kill Switch Check ==="
    echo "1. Connect to VPN"
    echo "2. Disconnect VPN"
    echo "3. Try to browse internet"
    echo "4. Internet should be BLOCKED (kill switch working)"
fi

echo ""
echo "=== Security Summary ==="
echo ""
echo "✅ = Secure"
echo "⚠️  = Needs attention"
echo "❌ = Not secure"
echo ""
echo "Run this script on both VPS and local PC for complete check!"

