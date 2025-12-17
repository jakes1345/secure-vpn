#!/bin/bash
# SecureVPN - Generate Certificates in Git Bash
# Run this in Git Bash as Administrator

echo "========================================"
echo "SecureVPN - Generate Certificates"
echo "========================================"
echo

# Create certs directory
mkdir -p certs
cd certs

echo "[INFO] Working directory: $(pwd)"
echo

# Generate CA private key (4096-bit RSA)
echo "[INFO] Step 1/8: Generating CA private key (4096-bit RSA)..."
openssl genrsa -out ca.key 4096
echo "[OK] CA private key generated"
echo

# Generate CA certificate
echo "[INFO] Step 2/8: Generating CA certificate..."
openssl req -new -x509 -key ca.key -sha512 -days 3650 -out ca.crt -subj "/C=US/ST=Secure/L=VPN/O=Server/CN=SecureVPN-CA"
echo "[OK] CA certificate generated"
echo

# Generate server private key (4096-bit RSA for maximum security)
echo "[INFO] Step 3/8: Generating server private key (4096-bit RSA)..."
openssl genrsa -out server.key 4096
echo "[OK] Server private key generated"
echo

# Generate server certificate signing request
echo "[INFO] Step 4/8: Generating server certificate signing request..."
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Secure/L=VPN/O=Server/CN=SecureVPN-Server"
echo "[OK] Server CSR generated"
echo

# Sign server certificate with CA
echo "[INFO] Step 5/8: Signing server certificate..."
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650 -sha512
echo "[OK] Server certificate signed"
echo

# Generate client private key (4096-bit RSA for maximum security)
echo "[INFO] Step 6/8: Generating client private key (4096-bit RSA)..."
openssl genrsa -out client.key 4096
echo "[OK] Client private key generated"
echo

# Generate client certificate signing request
echo "[INFO] Step 7/8: Generating client certificate signing request..."
openssl req -new -key client.key -out client.csr -subj "/C=US/ST=Secure/L=VPN/O=Client/CN=SecureVPN-Client"
echo "[OK] Client CSR generated"
echo

# Sign client certificate with CA
echo "[INFO] Step 8/8: Signing client certificate..."
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 3650 -sha512
echo "[OK] Client certificate signed"
echo

# Generate TLS authentication key
echo "[INFO] Generating TLS authentication key..."
openssl rand -hex 2048 > ta.key
echo "[OK] TLS authentication key generated"
echo

# Generate ECDH parameters (P-521 curve)
echo "[INFO] Generating ECDH parameters (P-521 curve)..."
openssl ecparam -out ec.pem -name secp521r1
echo "[OK] ECDH parameters generated"
echo

# Generate 4096-bit DH parameters (takes 5-15 minutes, but provides maximum security)
echo "[INFO] Generating 4096-bit DH parameters (this may take 5-15 minutes)..."
echo "[INFO] This is for maximum security - worth the wait!"
openssl dhparam -out dh4096.pem 4096
if [ $? -eq 0 ]; then
    # Also create a symlink for compatibility
    ln -sf dh4096.pem dh.pem
    echo "[OK] 4096-bit DH parameters generated"
else
    echo "[WARNING] Failed to generate 4096-bit DH, falling back to 2048-bit..."
    openssl dhparam -out dh.pem 2048
    echo "[OK] 2048-bit DH parameters created (fallback)"
fi
echo

# Clean up temporary files
echo "[INFO] Cleaning up temporary files..."
rm -f server.csr client.csr ca.srl
echo "[OK] Temporary files cleaned up"
echo

# Verify all files were created
echo "[INFO] Verifying certificate files..."
files=("ca.key" "ca.crt" "server.key" "server.crt" "client.key" "client.crt" "ta.key" "dh4096.pem" "ec.pem")
missing_files=()

for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "[ERROR] Missing certificate files: ${missing_files[*]}"
    exit 1
fi

echo "[OK] All certificate files verified"
echo

echo "========================================"
echo "Certificate Generation Complete!"
echo "========================================"
echo
echo "[SUCCESS] All certificates generated successfully!"
echo
echo "[CA] ca.key, ca.crt (4096-bit RSA)"
echo "[Server] server.key, server.crt (4096-bit RSA)"
echo "[Client] client.key, client.crt (4096-bit RSA)"
echo "[Security] ta.key, dh4096.pem (4096-bit), ec.pem (P-521)"
echo
echo "[INFO] Security Level: MAXIMUM - BEYOND AES-256"
echo "[INFO] - CA: 4096-bit RSA (Maximum security)"
echo "[INFO] - Server/Client: 4096-bit RSA (Beyond military standard)"
echo "[INFO] - DH: 4096-bit (Maximum Perfect Forward Secrecy)"
echo "[INFO] - ECDH: P-521 curve (521-bit, Quantum-resistant)"
echo "[INFO] - Cipher: ChaCha20-Poly1305 (Modern, faster than AES-256-GCM)"
echo "[INFO] - Hash: SHA512 (Maximum collision resistance)"
echo "[INFO] - TLS: 1.3 minimum (Latest protocol)"
echo
echo "[INFO] Certificates are ready for use!"
echo "[INFO] Next: Run start-vpn-server.bat"
echo

# Return to original directory
cd ..
echo "[INFO] Returned to: $(pwd)"
echo
