#!/usr/bin/env python3
"""
PhazeVPN Protocol - Custom Certificate Generator
EXPERIMENTAL - Use at your own risk!

This generates certificates SPECIFICALLY for PhazeVPN protocol.
These are SEPARATE from OpenVPN and WireGuard certificates.

⚠️  WARNING: This is an EXPERIMENTAL protocol
⚠️  Not audited by security experts
⚠️  Use at your own risk
"""

import os
import subprocess
import secrets
from pathlib import Path
from datetime import datetime, timedelta

# Experimental warning
EXPERIMENTAL_WARNING = """
╔═══════════════════════════════════════════════════════════════╗
║                   ⚠️  EXPERIMENTAL PROTOCOL  ⚠️                 ║
╠═══════════════════════════════════════════════════════════════╣
║  PhazeVPN Protocol is EXPERIMENTAL and UNVERIFIED             ║
║                                                               ║
║  • Not audited by security experts                           ║
║  • Not tested by trusted organizations                       ║
║  • May contain security vulnerabilities                       ║
║  • Use at your own risk                                      ║
║                                                               ║
║  For production use, we recommend:                            ║
║  • OpenVPN (audited and verified)                            ║
║  • WireGuard (audited by experts)                            ║
╚═══════════════════════════════════════════════════════════════╝
"""

def print_warning():
    """Print experimental warning"""
    print(EXPERIMENTAL_WARNING)
    print()

def generate_ca():
    """Generate PhazeVPN CA (Certificate Authority)"""
    print("🔐 Generating PhazeVPN CA (Certificate Authority)...")
    print("   ⚠️  EXPERIMENTAL - Use at your own risk!")
    print()
    
    certs_dir = Path(__file__).parent / 'phazevpn-certs'
    certs_dir.mkdir(exist_ok=True)
    
    ca_key = certs_dir / 'phazevpn-ca.key'
    ca_crt = certs_dir / 'phazevpn-ca.crt'
    
    # Generate CA private key - Using Ed25519 (modern, fast, secure)
    # Ed25519 is what WireGuard uses - much better than RSA!
    print("   [1/3] Generating CA private key (Ed25519 - modern standard)...")
    try:
        # Try Ed25519 first (modern, fast, secure - what WireGuard uses)
        subprocess.run([
            'openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(ca_key)
        ], check=True)
        print("      ✅ Using Ed25519 (modern standard - same as WireGuard)")
    except:
        # Fallback to RSA 4096 if Ed25519 not supported
        print("      ⚠️  Ed25519 not available, using RSA 4096 (older but still secure)")
        subprocess.run([
            'openssl', 'genrsa', '-out', str(ca_key), '4096'
        ], check=True)
    
    # Generate CA certificate
    print("   [2/3] Generating CA certificate...")
    subprocess.run([
        'openssl', 'req', '-new', '-x509', '-key', str(ca_key),
        '-out', str(ca_crt), '-days', '3650', '-sha512',
        '-subj', '/C=XX/ST=Experimental/L=PhazeVPN/O=PhazeVPN-Experimental/CN=PhazeVPN-Experimental-CA'
    ], check=True)
    
    # Add experimental warning to cert
    print("   [3/3] Adding experimental warning to certificate...")
    with open(ca_crt, 'a') as f:
        f.write('\n# ⚠️  EXPERIMENTAL - PhazeVPN Protocol Certificate\n')
        f.write('# Not audited - Use at your own risk\n')
    
    print("   ✅ PhazeVPN CA generated")
    print()
    return ca_key, ca_crt

def generate_server_cert(ca_key, ca_crt):
    """Generate PhazeVPN server certificate"""
    print("🔐 Generating PhazeVPN server certificate...")
    print("   ⚠️  EXPERIMENTAL - Use at your own risk!")
    print()
    
    certs_dir = Path(__file__).parent / 'phazevpn-certs'
    server_key = certs_dir / 'phazevpn-server.key'
    server_crt = certs_dir / 'phazevpn-server.crt'
    server_csr = certs_dir / 'phazevpn-server.csr'
    
    # Generate server private key - Using Ed25519 (modern standard)
    print("   [1/4] Generating server private key (Ed25519 - modern standard)...")
    try:
        # Try Ed25519 first (modern, fast, secure)
        subprocess.run([
            'openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(server_key)
        ], check=True)
        print("      ✅ Using Ed25519 (modern standard)")
    except:
        # Fallback to RSA 4096
        print("      ⚠️  Ed25519 not available, using RSA 4096")
        subprocess.run([
            'openssl', 'genrsa', '-out', str(server_key), '4096'
        ], check=True)
    
    # Generate server certificate signing request
    print("   [2/4] Generating server certificate request...")
    subprocess.run([
        'openssl', 'req', '-new', '-key', str(server_key),
        '-out', str(server_csr),
        '-subj', '/C=XX/ST=Experimental/L=PhazeVPN/O=PhazeVPN-Experimental/CN=PhazeVPN-Experimental-Server'
    ], check=True)
    
    # Sign server certificate
    print("   [3/4] Signing server certificate...")
    subprocess.run([
        'openssl', 'x509', '-req', '-in', str(server_csr),
        '-CA', str(ca_crt), '-CAkey', str(ca_key), '-CAcreateserial',
        '-out', str(server_crt), '-days', '365', '-sha512'
    ], check=True)
    
    # Add experimental warning
    print("   [4/4] Adding experimental warning...")
    with open(server_crt, 'a') as f:
        f.write('\n# ⚠️  EXPERIMENTAL - PhazeVPN Protocol Certificate\n')
        f.write('# Not audited - Use at your own risk\n')
    
    print("   ✅ PhazeVPN server certificate generated")
    print()
    return server_key, server_crt

def generate_client_cert(client_name, ca_key, ca_crt):
    """Generate PhazeVPN client certificate"""
    print(f"🔐 Generating PhazeVPN client certificate for '{client_name}'...")
    print("   ⚠️  EXPERIMENTAL - Use at your own risk!")
    print()
    
    certs_dir = Path(__file__).parent / 'phazevpn-certs'
    client_key = certs_dir / f'phazevpn-{client_name}.key'
    client_crt = certs_dir / f'phazevpn-{client_name}.crt'
    client_csr = certs_dir / f'phazevpn-{client_name}.csr'
    
    # Generate client private key - Using Ed25519 (modern standard)
    print("   [1/4] Generating client private key (Ed25519 - modern standard)...")
    try:
        # Try Ed25519 first (modern, fast, secure - same as WireGuard)
        subprocess.run([
            'openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(client_key)
        ], check=True)
        print("      ✅ Using Ed25519 (modern standard - same as WireGuard)")
    except:
        # Fallback to RSA 4096
        print("      ⚠️  Ed25519 not available, using RSA 4096")
        subprocess.run([
            'openssl', 'genrsa', '-out', str(client_key), '4096'
        ], check=True)
    
    # Generate client certificate signing request
    print("   [2/4] Generating client certificate request...")
    subprocess.run([
        'openssl', 'req', '-new', '-key', str(client_key),
        '-out', str(client_csr),
        '-subj', f'/C=XX/ST=Experimental/L=PhazeVPN/O=PhazeVPN-Experimental/CN=PhazeVPN-Experimental-Client-{client_name}'
    ], check=True)
    
    # Sign client certificate
    print("   [3/4] Signing client certificate...")
    subprocess.run([
        'openssl', 'x509', '-req', '-in', str(client_csr),
        '-CA', str(ca_crt), '-CAkey', str(ca_key), '-CAcreateserial',
        '-out', str(client_crt), '-days', '365', '-sha512'
    ], check=True)
    
    # Add experimental warning
    print("   [4/4] Adding experimental warning...")
    with open(client_crt, 'a') as f:
        f.write('\n# ⚠️  EXPERIMENTAL - PhazeVPN Protocol Certificate\n')
        f.write('# Not audited - Use at your own risk\n')
        f.write(f'# Client: {client_name}\n')
        f.write(f'# Generated: {datetime.now().isoformat()}\n')
    
    print("   ✅ PhazeVPN client certificate generated")
    print()
    return client_key, client_crt

def generate_session_key():
    """Generate PhazeVPN session encryption key"""
    print("🔐 Generating PhazeVPN session encryption key...")
    print("   ⚠️  EXPERIMENTAL - Use at your own risk!")
    print()
    
    certs_dir = Path(__file__).parent / 'phazevpn-certs'
    session_key = certs_dir / 'phazevpn-session.key'
    
    # Generate 256-bit random key using cryptographically secure RNG
    # Using secrets module (Python's secure RNG - same as WireGuard uses)
    key_bytes = secrets.token_bytes(32)  # 256 bits (AES-256 / ChaCha20 key size)
    with open(session_key, 'wb') as f:
        f.write(key_bytes)
    
    # Note: secrets.token_bytes() uses os.urandom() which is cryptographically secure
    # This is the SAME method WireGuard uses for key generation
    
    os.chmod(session_key, 0o600)  # Secure permissions
    
    print("   ✅ PhazeVPN session key generated")
    print()
    return session_key

def main():
    """Main function"""
    print_warning()
    
    print("="*60)
    print("PhazeVPN Protocol - Custom Certificate Generator")
    print("="*60)
    print()
    print("This generates certificates SPECIFICALLY for PhazeVPN protocol.")
    print("These are SEPARATE from OpenVPN and WireGuard certificates.")
    print()
    
    import sys
    if len(sys.argv) > 1:
        client_name = sys.argv[1]
        print(f"Generating certificates for client: {client_name}")
        print()
    else:
        client_name = None
        print("Generating CA and server certificates...")
        print()
    
    # Generate CA
    ca_key, ca_crt = generate_ca()
    
    # Generate server cert
    server_key, server_crt = generate_server_cert(ca_key, ca_crt)
    
    # Generate session key
    session_key = generate_session_key()
    
    # Generate client cert if name provided
    if client_name:
        client_key, client_crt = generate_client_cert(client_name, ca_key, ca_crt)
        print("="*60)
        print("✅ CLIENT CERTIFICATE GENERATED")
        print("="*60)
        print(f"Client: {client_name}")
        print(f"Key: {client_key}")
        print(f"Cert: {client_crt}")
        print()
        print("⚠️  REMEMBER: This is EXPERIMENTAL - Use at your own risk!")
    else:
        print("="*60)
        print("✅ CA AND SERVER CERTIFICATES GENERATED")
        print("="*60)
        print(f"CA Key: {ca_key}")
        print(f"CA Cert: {ca_crt}")
        print(f"Server Key: {server_key}")
        print(f"Server Cert: {server_crt}")
        print(f"Session Key: {session_key}")
        print()
        print("⚠️  REMEMBER: This is EXPERIMENTAL - Use at your own risk!")
        print()
        print("To generate a client certificate, run:")
        print(f"  python3 {__file__} CLIENT_NAME")

if __name__ == '__main__':
    main()

