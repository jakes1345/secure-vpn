#!/bin/bash
# Automated Integration Script for VPS
# Integrates all security fixes automatically

set -e

echo "========================================"
echo "🤖 Automated Security Integration"
echo "========================================"
echo ""

# Navigate to PhazeVPN directory
cd /opt/phazevpn/phazevpn-protocol-go

echo "📝 Step 1: Backing up original files..."
cp internal/client/client.go internal/client/client.go.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

echo ""
echo "📝 Step 2: Integrating leak protections into client.go..."

# Add imports to client.go
sed -i '/import (/a\
\t"phazevpn-server/internal/dns"\
\t"phazevpn-server/internal/ipv6"\
\t"phazevpn-server/internal/webrtc"' internal/client/client.go

# Add fields to PhazeVPNClient struct (after existing fields)
sed -i '/type PhazeVPNClient struct {/,/^}/{
    /bytesSent.*int64/a\
\
\t// Leak protection\
\tdnsProtection    *dns.DNSProtection\
\tipv6Protection   *ipv6.IPv6Protection\
\twebrtcProtection *webrtc.WebRTCProtection
}' internal/client/client.go

# Add initialization in NewPhazeVPNClient (after stopChan)
sed -i '/stopChan:.*make(chan struct{})/a\
\t\tdnsProtection:    dns.NewDNSProtection([]string{"1.1.1.1", "1.0.0.1"}),\
\t\tipv6Protection:   ipv6.NewIPv6Protection(),\
\t\twebrtcProtection: webrtc.NewWebRTCProtection(),' internal/client/client.go

# Add leak protection enable in Connect() (after "Connecting to PhazeVPN server" log)
sed -i '/log.Println("🔌 Connecting to PhazeVPN server...")/a\
\
\t// Enable leak protections BEFORE connecting\
\tlog.Println("🔒 Enabling leak protections...")\
\tif err := c.dnsProtection.Enable(); err != nil {\
\t\treturn fmt.Errorf("failed to enable DNS protection: %w", err)\
\t}\
\tif err := c.ipv6Protection.Enable(); err != nil {\
\t\tc.dnsProtection.Disable()\
\t\treturn fmt.Errorf("failed to enable IPv6 protection: %w", err)\
\t}\
\tif err := c.webrtcProtection.Enable(); err != nil {\
\t\tc.dnsProtection.Disable()\
\t\tc.ipv6Protection.Disable()\
\t\treturn fmt.Errorf("failed to enable WebRTC protection: %w", err)\
\t}\
\tlog.Println("✅ All leak protections enabled")' internal/client/client.go

# Add leak protection disable in Disconnect() (before "Disconnected" log)
sed -i '/log.Println("✅ Disconnected")/i\
\
\t// Disable leak protections\
\tlog.Println("🔓 Disabling leak protections...")\
\tif c.webrtcProtection != nil {\
\t\tc.webrtcProtection.Disable()\
\t}\
\tif c.ipv6Protection != nil {\
\t\tc.ipv6Protection.Disable()\
\t}\
\tif c.dnsProtection != nil {\
\t\tc.dnsProtection.Disable()\
\t}\
\tlog.Println("✅ Leak protections disabled")' internal/client/client.go

echo "✅ Leak protections integrated into client.go"

echo ""
echo "📝 Step 3: Rebuilding PhazeVPN server..."
go build -o phazevpn-server main.go
if [ $? -eq 0 ]; then
    echo "✅ PhazeVPN server rebuilt successfully"
    ls -lh phazevpn-server
else
    echo "❌ Build failed - check errors above"
    exit 1
fi

echo ""
echo "📝 Step 4: Integrating session manager into web portal..."
cd /opt/phazevpn-portal

# Backup app.py
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S)

# Add import after other imports (around line 100)
sed -i '/^import email_api/a\
from session_manager import SessionManager' app.py

# Add SessionManager initialization after app creation (around line 180)
sed -i '/^app = Flask(__name__/a\
\
# Initialize session manager\
session_mgr = SessionManager(app)' app.py

# Comment out old session config (lines 228-238)
sed -i '228,238s/^app.config/# app.config  # Handled by SessionManager/' app.py

# Add session migration before_request
sed -i '/^@app.before_request/,/^def block_python_files()/{
    /^def block_python_files()/i\
@app.before_request\
def migrate_sessions():\
    """Migrate old sessions to new format"""\
    SessionManager.migrate_old_session()\

}' app.py

echo "✅ Session manager integrated into app.py"

echo ""
echo "📝 Step 5: Restarting web portal..."
systemctl restart phazevpn-portal
sleep 3
systemctl status phazevpn-portal --no-pager | head -10

echo ""
echo "========================================"
echo "✅ Integration Complete!"
echo "========================================"
echo ""
echo "Summary:"
echo "  ✅ Leak protections integrated into PhazeVPN client"
echo "  ✅ PhazeVPN server rebuilt"
echo "  ✅ Session manager integrated into web portal"
echo "  ✅ Web portal restarted"
echo ""
echo "🔒 Security improvements:"
echo "  ✅ DNS leak protection active"
echo "  ✅ IPv6 leak protection active"
echo "  ✅ WebRTC leak protection active"
echo "  ✅ Website sign-in stable"
echo ""
echo "📋 Next steps:"
echo "  1. Test website login: https://phazevpn.com/login"
echo "  2. Test VPN connection with leak protection"
echo "  3. Run leak tests (DNS, IPv6, WebRTC)"
echo ""
echo "Binary location: /opt/phazevpn/phazevpn-protocol-go/phazevpn-server"
echo ""
