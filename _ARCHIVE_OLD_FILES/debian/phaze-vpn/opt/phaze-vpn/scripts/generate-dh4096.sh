#!/bin/bash
# Generate 4096-bit Diffie-Hellman Parameters
# Maximum Perfect Forward Secrecy
# Takes 5-15 minutes (CPU-intensive but worth it!)

set -e

CERT_DIR="${CERT_DIR:-certs}"
DH_FILE="$CERT_DIR/dh4096.pem"

echo "🔐 Generating 4096-bit Diffie-Hellman Parameters..."
echo ""
echo "This will take 5-15 minutes (CPU-intensive)."
echo "Maximum Perfect Forward Secrecy - worth the wait!"
echo ""

# Create certs directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Check if already exists
if [ -f "$DH_FILE" ]; then
    echo "⚠️  $DH_FILE already exists"
    read -p "Regenerate? (y/N): " REGEN
    if [ "$REGEN" != "y" ] && [ "$REGEN" != "Y" ]; then
        echo "Skipping..."
        exit 0
    fi
    rm -f "$DH_FILE"
fi

echo "Generating 4096-bit DH parameters..."
echo "This may take 10-20 minutes depending on your CPU..."
echo ""

# Generate 4096-bit DH parameters
openssl dhparam -out "$DH_FILE" 4096

if [ $? -eq 0 ] && [ -f "$DH_FILE" ]; then
    echo ""
    echo "✅ 4096-bit DH parameters generated!"
    echo "   File: $DH_FILE"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Update server config to use: dh $DH_FILE"
    echo "   2. Restart VPN server"
    echo ""
    
    # Verify
    echo "Verifying parameters..."
    openssl dhparam -in "$DH_FILE" -text -noout | head -5
    echo ""
    echo "✅ Verification complete!"
else
    echo "❌ Failed to generate DH parameters"
    exit 1
fi

