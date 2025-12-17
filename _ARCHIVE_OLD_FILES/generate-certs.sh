#!/bin/bash
# Simple VPN Certificate Generator
# Easy to modify - just change the variables at the top!

# ============================================
# CUSTOMIZE THESE SETTINGS
# ============================================
CA_NAME="MyVPN-CA"
SERVER_NAME="MyVPN-Server"
COUNTRY="CH"
STATE="Zurich"
CITY="Zurich"
ORG="MyVPN"
CA_VALIDITY=3650  # 10 years
CERT_VALIDITY=365  # 1 year
KEY_SIZE=4096      # 4096-bit RSA for maximum security (beyond AES-256)
DH_SIZE=4096       # 4096-bit DH parameters for maximum security

# ============================================
# SCRIPT STARTS HERE
# ============================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SCRIPT_DIR/certs"

echo "=========================================="
echo "VPN Certificate Generator"
echo "=========================================="
echo ""

# Create certs directory
mkdir -p "$CERTS_DIR"
cd "$CERTS_DIR"

echo "[1/8] Generating CA private key (${KEY_SIZE}-bit)..."
openssl genrsa -out ca.key $KEY_SIZE

echo "[2/8] Generating CA certificate..."
openssl req -new -x509 -key ca.key -sha512 -days $CA_VALIDITY -out ca.crt \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$CA_NAME"

echo "[3/8] Generating server private key (${KEY_SIZE}-bit)..."
openssl genrsa -out server.key $KEY_SIZE

echo "[4/8] Generating server certificate request..."
openssl req -new -key server.key -out server.csr \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$SERVER_NAME"

echo "[5/8] Signing server certificate..."
if [ -f "$SCRIPT_DIR/certs/openssl-server.cnf" ]; then
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out server.crt -days $CERT_VALIDITY -sha512 \
        -extensions v3_req -extfile "$SCRIPT_DIR/certs/openssl-server.cnf"
else
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out server.crt -days $CERT_VALIDITY -sha512
fi

echo "[6/8] Generating Diffie-Hellman parameters (${DH_SIZE}-bit)..."
echo "      (This may take a few minutes for 4096-bit)"
openssl dhparam -out dh.pem $DH_SIZE

echo "[7/8] Generating TLS authentication key..."
openvpn --genkey --secret ta.key 2>/dev/null || \
    openssl rand -hex 32 > ta.key

echo "[8/8] Cleaning up temporary files..."
rm -f server.csr client.csr ca.srl

echo ""
echo "=========================================="
echo "✓ Certificates generated successfully!"
echo "=========================================="
echo ""
echo "Files created in: $CERTS_DIR"
echo "  - ca.crt, ca.key (Certificate Authority)"
echo "  - server.crt, server.key (Server certificate)"
echo "  - dh.pem (Diffie-Hellman parameters)"
echo "  - ta.key (TLS authentication key)"
echo ""
echo "Next step: Run './manage-vpn.sh add-client <name>' to create client certificates"
echo ""

cd "$SCRIPT_DIR"

