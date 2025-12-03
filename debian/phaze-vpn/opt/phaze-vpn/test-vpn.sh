#!/bin/bash
# VPN Testing and Validation Script

set -e

VPN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/secure-vpn"
ACTUAL_DIR="${VPN_DIR}"

echo "=========================================="
echo "SecureVPN System Test"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Test function
test_check() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing $name... "
    
    if eval "$command" >/dev/null 2>&1; then
        echo "✓ PASS"
        return 0
    else
        echo "✗ FAIL"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Check if running as root for some tests
if [ "$EUID" -eq 0 ]; then
    ROOT_MODE=1
else
    ROOT_MODE=0
    echo "⚠️  Running in non-root mode (some tests skipped)"
    echo ""
fi

# File existence tests
echo "📁 File Checks:"
test_check "VPN directory exists" "[ -d '$ACTUAL_DIR' ]"
test_check "Config directory exists" "[ -d '$ACTUAL_DIR/config' ]"
test_check "Certs directory exists" "[ -d '$ACTUAL_DIR/certs' ]"
test_check "Scripts directory exists" "[ -d '$ACTUAL_DIR/scripts' ]"
test_check "Main VPN manager exists" "[ -f '$ACTUAL_DIR/vpn-manager.py' ]"
test_check "GUI application exists" "[ -f '$ACTUAL_DIR/vpn-gui.py' ]"
test_check "Download server exists" "[ -f '$ACTUAL_DIR/client-download-server.py' ]"
test_check "Server config exists" "[ -f '$ACTUAL_DIR/config/server.conf' ]"
echo ""

# Executable permissions
echo "🔧 Permission Checks:"
test_check "VPN manager is executable" "[ -x '$ACTUAL_DIR/vpn-manager.py' ]"
test_check "GUI is executable" "[ -x '$ACTUAL_DIR/vpn-gui.py' ]"
test_check "Generate certs script is executable" "[ -x '$ACTUAL_DIR/generate-certs.sh' ]"
test_check "Setup routing script is executable" "[ -x '$ACTUAL_DIR/setup-routing.sh' ]"
echo ""

# Certificate checks
echo "🔐 Certificate Checks:"
if [ -f "$ACTUAL_DIR/certs/ca.crt" ]; then
    test_check "CA certificate exists" "true"
    test_check "CA certificate is valid" "openssl x509 -in '$ACTUAL_DIR/certs/ca.crt' -text -noout >/dev/null 2>&1"
else
    echo "⚠️  CA certificate not found (run generate-certs.sh)"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "$ACTUAL_DIR/certs/server.crt" ]; then
    test_check "Server certificate exists" "true"
else
    echo "⚠️  Server certificate not found"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "$ACTUAL_DIR/certs/dh.pem" ] || [ -f "$ACTUAL_DIR/certs/dh4096.pem" ]; then
    test_check "DH parameters exist" "true"
else
    echo "⚠️  DH parameters not found"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Dependency checks
echo "📦 Dependency Checks:"
test_check "OpenVPN installed" "command -v openvpn"
test_check "OpenSSL installed" "command -v openssl"
test_check "Python3 installed" "command -v python3"
test_check "Python3 tkinter available" "python3 -c 'import tkinter' 2>/dev/null"

if python3 -c "import psutil" 2>/dev/null; then
    echo "✓ psutil installed (optional)"
else
    echo "⚠️  psutil not installed (optional, for system metrics)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Service checks (if installed)
if [ -f "/etc/systemd/system/secure-vpn.service" ]; then
    echo "⚙️  Service Checks:"
    if [ "$ROOT_MODE" -eq 1 ]; then
        test_check "Systemd service exists" "systemctl list-unit-files | grep -q secure-vpn"
        if systemctl is-active --quiet secure-vpn 2>/dev/null; then
            echo "✓ VPN service is running"
        else
            echo "⚠️  VPN service is not running"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "⚠️  Service checks skipped (need root)"
    fi
    echo ""
fi

# Network checks
echo "🌐 Network Checks:"
if [ "$ROOT_MODE" -eq 1 ]; then
    IP_FORWARD=$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null || echo "0")
    if [ "$IP_FORWARD" = "1" ]; then
        echo "✓ IP forwarding is enabled"
    else
        echo "⚠️  IP forwarding is disabled (clients won't have internet)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  Network checks skipped (need root)"
fi
echo ""

# Configuration validation
echo "⚙️  Configuration Checks:"
if [ -f "$ACTUAL_DIR/config/server.conf" ]; then
    # Check for required settings
    if grep -q "cipher.*CHACHA20-POLY1305\|cipher.*AES-256-GCM" "$ACTUAL_DIR/config/server.conf"; then
        echo "✓ Encryption cipher configured"
    else
        echo "⚠️  Encryption cipher not found in config"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    if grep -q "tls-version-min.*1.3\|tls-version-min.*1.2" "$ACTUAL_DIR/config/server.conf"; then
        echo "✓ TLS version configured"
    else
        echo "⚠️  TLS version not configured"
        WARNINGS=$((WARNINGS + 1))
    fi
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo "✅ All tests passed! System is ready."
        exit 0
    else
        echo "⚠️  Tests passed with warnings. Review above."
        exit 0
    fi
else
    echo "❌ Some tests failed. Please fix errors above."
    exit 1
fi

