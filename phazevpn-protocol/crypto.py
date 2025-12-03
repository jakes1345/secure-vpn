#!/usr/bin/env python3
"""
PhazeVPN Protocol - Cryptographic Functions
Custom encryption/decryption for PhazeVPN Protocol
"""

import os
import hashlib
import hmac
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305, AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization
import base64

# Cipher constants
CIPHER_CHACHA20 = 0x01
CIPHER_AES256 = 0x02

class PhazeVPNCrypto:
    """Custom cryptographic functions for PhazeVPN Protocol"""
    
    def __init__(self):
        self.cipher_type = CIPHER_CHACHA20
        self.private_key = None
        self.public_key = None
        self.shared_secret = None
        self.session_key = None
        self.session_nonce = 0
        
    def generate_keypair(self):
        """Generate X25519 keypair for key exchange"""
        self.private_key = X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        return self.public_key
    
    def get_public_key_bytes(self):
        """Get public key as bytes"""
        if not self.public_key:
            return None
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def derive_shared_secret(self, peer_public_key_bytes):
        """Derive shared secret from peer's public key"""
        if not self.private_key:
            raise ValueError("Private key not generated")
        
        peer_public_key = X25519PublicKey.from_public_bytes(peer_public_key_bytes)
        self.shared_secret = self.private_key.exchange(peer_public_key)
        return self.shared_secret
    
    def derive_session_key(self, salt=None, info=b'phazevpn-session'):
        """Derive session key from shared secret using HKDF"""
        if not self.shared_secret:
            raise ValueError("Shared secret not derived")
        
        if salt is None:
            salt = os.urandom(32)
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            info=info,
            backend=default_backend()
        )
        
        self.session_key = hkdf.derive(self.shared_secret)
        return self.session_key, salt
    
    def encrypt_packet(self, plaintext, nonce=None):
        """Encrypt packet using ChaCha20-Poly1305 or AES-256-GCM"""
        if not self.session_key:
            raise ValueError("Session key not derived")
        
        if nonce is None:
            nonce = os.urandom(12)  # 96-bit nonce
        
        try:
            if self.cipher_type == CIPHER_CHACHA20:
                cipher = ChaCha20Poly1305(self.session_key)
            else:
                cipher = AESGCM(self.session_key)
            
            ciphertext = cipher.encrypt(nonce, plaintext, None)
            return nonce + ciphertext  # Nonce + ciphertext + auth tag
        except Exception as e:
            # Fallback to AES if ChaCha20 fails
            if self.cipher_type == CIPHER_CHACHA20:
                self.cipher_type = CIPHER_AES256
                return self.encrypt_packet(plaintext, nonce)
            raise
    
    def decrypt_packet(self, encrypted_data):
        """Decrypt packet"""
        if not self.session_key:
            raise ValueError("Session key not derived")
        
        if len(encrypted_data) < 28:  # 12 nonce + 16 auth tag + at least some data
            raise ValueError("Encrypted data too short")
        
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        try:
            if self.cipher_type == CIPHER_CHACHA20:
                cipher = ChaCha20Poly1305(self.session_key)
            else:
                cipher = AESGCM(self.session_key)
            
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            return plaintext
        except Exception as e:
            # Try other cipher if current one fails
            if self.cipher_type == CIPHER_CHACHA20:
                self.cipher_type = CIPHER_AES256
                return self.decrypt_packet(encrypted_data)
            else:
                self.cipher_type = CIPHER_CHACHA20
                return self.decrypt_packet(encrypted_data)
    
    def hash_password(self, password, salt=None):
        """Hash password using PBKDF2"""
        if salt is None:
            salt = os.urandom(32)
        
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return key, salt
    
    def verify_password(self, password, stored_key, salt):
        """Verify password against stored hash"""
        computed_key, _ = self.hash_password(password, salt)
        return hmac.compare_digest(computed_key, stored_key)
    
    def generate_session_token(self):
        """Generate random session token"""
        return os.urandom(32)
    
    def hmac_sign(self, data, key=None):
        """Generate HMAC signature"""
        if key is None:
            key = self.session_key
        if not key:
            raise ValueError("Key not available")
        return hmac.new(key, data, hashlib.sha256).digest()
    
    def verify_hmac(self, data, signature, key=None):
        """Verify HMAC signature"""
        if key is None:
            key = self.session_key
        if not key:
            raise ValueError("Key not available")
        expected = hmac.new(key, data, hashlib.sha256).digest()
        return hmac.compare_digest(expected, signature)

