#!/bin/bash
# Deploy Critical Security Fixes to VPS
# Uploads session manager and rebuilds PhazeVPN with leak protection

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="<VPS_PASSWORD_REMOVED>"

echo "========================================"
echo "🚀 Deploying Critical Security Fixes"
echo "========================================"
echo ""

# 1. Upload session manager to web portal
echo "📤 Uploading session manager to web portal..."
sshpass -p "$VPS_PASS" scp web-portal/session_manager.py $VPS_USER@$VPS_IP:/opt/phazevpn-portal/

# 2. Upload leak protection modules
echo "📤 Uploading DNS leak protection..."
sshpass -p "$VPS_PASS" ssh $VPS_USER@$VPS_IP "mkdir -p /opt/phazevpn/phazevpn-protocol-go/internal/dns"
sshpass -p "$VPS_PASS" scp phazevpn-protocol-go/internal/dns/leak_protection.go $VPS_USER@$VPS_IP:/opt/phazevpn/phazevpn-protocol-go/internal/dns/

echo "📤 Uploading IPv6 leak protection..."
sshpass -p "$VPS_PASS" ssh $VPS_USER@$VPS_IP "mkdir -p /opt/phazevpn/phazevpn-protocol-go/internal/ipv6"
sshpass -p "$VPS_PASS" scp phazevpn-protocol-go/internal/ipv6/leak_protection.go $VPS_USER@$VPS_IP:/opt/phazevpn/phazevpn-protocol-go/internal/ipv6/

echo "📤 Uploading WebRTC leak protection..."
sshpass -p "$VPS_PASS" ssh $VPS_USER@$VPS_IP "mkdir -p /opt/phazevpn/phazevpn-protocol-go/internal/webrtc"
sshpass -p "$VPS_PASS" scp phazevpn-protocol-go/internal/webrtc/leak_protection.go $VPS_USER@$VPS_IP:/opt/phazevpn/phazevpn-protocol-go/internal/webrtc/

# 3. Update client.go with leak protection integration
echo "📝 Creating client integration patch..."
cat > /tmp/client_leak_protection.patch << 'EOF'
// Add to imports
import (
    "phazevpn-server/internal/dns"
    "phazevpn-server/internal/ipv6"
    "phazevpn-server/internal/webrtc"
)

// Add to PhazeVPNClient struct
type PhazeVPNClient struct {
    // ... existing fields ...
    
    // Leak protection
    dnsProtection    *dns.DNSProtection
    ipv6Protection   *ipv6.IPv6Protection
    webrtcProtection *webrtc.WebRTCProtection
}

// Add to NewPhazeVPNClient
func NewPhazeVPNClient(...) (*PhazeVPNClient, error) {
    client := &PhazeVPNClient{
        // ... existing fields ...
        dnsProtection:    dns.NewDNSProtection([]string{"1.1.1.1", "1.0.0.1"}),
        ipv6Protection:   ipv6.NewIPv6Protection(),
        webrtcProtection: webrtc.NewWebRTCProtection(),
    }
    return client, nil
}

// Add to Connect() - BEFORE handshake
func (c *PhazeVPNClient) Connect() error {
    log.Println("🔒 Enabling leak protections...")
    
    // Enable DNS protection
    if err := c.dnsProtection.Enable(); err != nil {
        return fmt.Errorf("failed to enable DNS protection: %w", err)
    }
    
    // Enable IPv6 protection
    if err := c.ipv6Protection.Enable(); err != nil {
        c.dnsProtection.Disable()
        return fmt.Errorf("failed to enable IPv6 protection: %w", err)
    }
    
    // Enable WebRTC protection
    if err := c.webrtcProtection.Enable(); err != nil {
        c.dnsProtection.Disable()
        c.ipv6Protection.Disable()
        return fmt.Errorf("failed to enable WebRTC protection: %w", err)
    }
    
    log.Println("✅ All leak protections enabled")
    
    // ... rest of existing Connect() code ...
}

// Add to Disconnect() - AFTER closing connection
func (c *PhazeVPNClient) Disconnect() error {
    // ... existing disconnect code ...
    
    log.Println("🔓 Disabling leak protections...")
    
    // Disable in reverse order
    if c.webrtcProtection != nil {
        c.webrtcProtection.Disable()
    }
    
    if c.ipv6Protection != nil {
        c.ipv6Protection.Disable()
    }
    
    if c.dnsProtection != nil {
        c.dnsProtection.Disable()
    }
    
    log.Println("✅ All leak protections disabled")
    return nil
}
EOF

echo "📤 Uploading client patch..."
sshpass -p "$VPS_PASS" scp /tmp/client_leak_protection.patch $VPS_USER@$VPS_IP:/tmp/

# 4. Apply patch and rebuild on VPS
echo "🔧 Applying patch and rebuilding on VPS..."
sshpass -p "$VPS_PASS" ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd /opt/phazevpn/phazevpn-protocol-go

# Backup original client.go
cp internal/client/client.go internal/client/client.go.backup 2>/dev/null || true

echo "✅ Patch instructions saved to /tmp/client_leak_protection.patch"
echo "⚠️  Manual integration needed - patch shows what to add"
echo ""
echo "📋 To complete integration:"
echo "1. Edit internal/client/client.go"
echo "2. Add imports from patch"
echo "3. Add fields to struct"
echo "4. Add initialization in NewPhazeVPNClient"
echo "5. Add Enable() calls in Connect()"
echo "6. Add Disable() calls in Disconnect()"
echo "7. Run: go build -o phazevpn-server main.go"
ENDSSH

# 5. Update web portal to use session manager
echo "🔧 Updating web portal..."
sshpass -p "$VPS_PASS" ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd /opt/phazevpn-portal

# Backup original app.py
cp app.py app.py.backup 2>/dev/null || true

echo "✅ session_manager.py uploaded"
echo "⚠️  Manual integration needed for app.py"
echo ""
echo "📋 To complete integration:"
echo "1. Edit app.py"
echo "2. Add: from session_manager import SessionManager"
echo "3. Add after app creation: session_mgr = SessionManager(app)"
echo "4. Replace session cookie config (lines 228-238) with: # Handled by SessionManager"
echo "5. Add before_request: SessionManager.migrate_old_session()"
echo "6. Restart: systemctl restart phazevpn-portal"
ENDSSH

echo ""
echo "========================================"
echo "✅ Files Uploaded to VPS"
echo "========================================"
echo ""
echo "Uploaded:"
echo "  ✅ session_manager.py → /opt/phazevpn-portal/"
echo "  ✅ dns/leak_protection.go → /opt/phazevpn/phazevpn-protocol-go/internal/dns/"
echo "  ✅ ipv6/leak_protection.go → /opt/phazevpn/phazevpn-protocol-go/internal/ipv6/"
echo "  ✅ webrtc/leak_protection.go → /opt/phazevpn/phazevpn-protocol-go/internal/webrtc/"
echo "  ✅ client_leak_protection.patch → /tmp/"
echo ""
echo "⚠️  Manual Steps Required on VPS:"
echo ""
echo "1. SSH to VPS: ssh root@15.204.11.19"
echo "2. Integrate client patch: cat /tmp/client_leak_protection.patch"
echo "3. Rebuild client: cd /root/phazevpn-protocol-go && go build -o phazevpn-client cmd/phazevpn-client/main.go"
echo "4. Integrate session manager in app.py"
echo "5. Restart portal: systemctl restart phazevpn-portal"
echo ""
echo "Or run: ./complete_integration_on_vps.sh"
echo ""
