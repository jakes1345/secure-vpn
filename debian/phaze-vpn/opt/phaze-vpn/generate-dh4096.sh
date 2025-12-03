#!/bin/bash
# Generate 4096-bit Diffie-Hellman parameters for maximum security
# This takes 5-15 minutes but provides the strongest possible security

echo "=========================================="
echo "Generating 4096-bit DH Parameters"
echo "=========================================="
echo ""
echo "This will take 5-15 minutes..."
echo "4096-bit DH provides maximum Perfect Forward Secrecy"
echo ""

cd "$(dirname "$0")"
mkdir -p certs
cd certs

echo "[INFO] Generating 4096-bit DH parameters..."
echo "[INFO] This is CPU-intensive but worth it for maximum security!"
echo ""

openssl dhparam -out dh4096.pem 4096

if [ $? -eq 0 ]; then
    # Create symlink for compatibility
    ln -sf dh4096.pem dh.pem
    echo ""
    echo "=========================================="
    echo "✓ 4096-bit DH parameters generated!"
    echo "=========================================="
    echo ""
    echo "File: certs/dh4096.pem"
    echo "Symlink: certs/dh.pem (for compatibility)"
    echo ""
    echo "Your VPN now uses maximum security DH parameters!"
else
    echo ""
    echo "[ERROR] Failed to generate 4096-bit DH parameters"
    echo "[INFO] Falling back to 2048-bit..."
    openssl dhparam -out dh.pem 2048
    echo "[OK] 2048-bit DH parameters created (fallback)"
fi

cd ..

