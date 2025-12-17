#!/usr/bin/env python3
"""
PhazeVPN Protocol - Certificate Manager
Integrates with OpenVPN certificate system
"""

import os
import subprocess
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

class PhazeVPNCertManager:
    """Manage certificates for PhazeVPN Protocol using OpenVPN certs"""
    
    def __init__(self, vpn_dir='/opt/secure-vpn'):
        self.vpn_dir = Path(vpn_dir)
        self.certs_dir = self.vpn_dir / 'certs'
        self.client_configs_dir = self.vpn_dir / 'client-configs'
    
    def get_ca_certificate(self):
        """Get CA certificate"""
        ca_crt = self.certs_dir / 'ca.crt'
        if ca_crt.exists():
            with open(ca_crt, 'rb') as f:
                return x509.load_pem_x509_certificate(f.read(), default_backend())
        return None
    
    def get_client_certificate(self, client_name):
        """Get client certificate"""
        client_crt = self.certs_dir / f'{client_name}.crt'
        if client_crt.exists():
            with open(client_crt, 'rb') as f:
                return x509.load_pem_x509_certificate(f.read(), default_backend())
        return None
    
    def get_client_key(self, client_name):
        """Get client private key"""
        client_key = self.certs_dir / f'{client_name}.key'
        if client_key.exists():
            with open(client_key, 'rb') as f:
                return serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
        return None
    
    def verify_client_certificate(self, client_name, cert_data):
        """Verify client certificate against CA"""
        try:
            ca_cert = self.get_ca_certificate()
            if not ca_cert:
                return False
            
            # Load provided certificate
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Verify signature
            ca_public_key = ca_cert.public_key()
            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                cert.signature_algorithm
            )
            
            # Check CN matches
            for attr in cert.subject:
                if attr.oid._name == 'commonName':
                    if attr.value == client_name:
                        return True
            
            return False
        except Exception as e:
            print(f"Certificate verification error: {e}")
            return False
    
    def generate_client_certificate(self, client_name):
        """Generate client certificate using OpenVPN system"""
        if not (self.certs_dir / 'ca.crt').exists():
            raise ValueError("CA certificate not found. Run generate-certs.sh first")
        
        client_key = self.certs_dir / f'{client_name}.key'
        client_crt = self.certs_dir / f'{client_name}.crt'
        client_csr = self.certs_dir / f'{client_name}.csr'
        
        # Generate key
        subprocess.run(['openssl', 'genrsa', '-out', str(client_key), '4096'], check=True)
        
        # Generate CSR
        subprocess.run([
            'openssl', 'req', '-new', '-key', str(client_key),
            '-out', str(client_csr),
            '-subj', f'/C=US/ST=Secure/L=VPN/O=Client/CN={client_name}'
        ], check=True)
        
        # Sign certificate
        ca_crt = self.certs_dir / 'ca.crt'
        ca_key = self.certs_dir / 'ca.key'
        openssl_cnf = self.vpn_dir / 'certs' / 'openssl-client.cnf'
        
        cmd = [
            'openssl', 'x509', '-req', '-in', str(client_csr),
            '-CA', str(ca_crt), '-CAkey', str(ca_key),
            '-CAcreateserial', '-out', str(client_crt),
            '-days', '365', '-sha512'
        ]
        
        if openssl_cnf.exists():
            cmd.extend(['-extensions', 'v3_req', '-extfile', str(openssl_cnf)])
        
        subprocess.run(cmd, check=True)
        
        # Clean up CSR
        if client_csr.exists():
            client_csr.unlink()
        
        return client_crt.exists()

