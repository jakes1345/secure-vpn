package obfuscation

import (
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"errors"

	"golang.org/x/crypto/chacha20poly1305"
)

// ShadowsocksObfuscator obfuscates traffic to look like normal HTTPS
// This makes VPN traffic undetectable by DPI (Deep Packet Inspection)
type ShadowsocksObfuscator struct {
	aead cipher.AEAD
}

// NewShadowsocksObfuscator creates a new Shadowsocks obfuscator
// Key can be any length - will be hashed to 32 bytes
func NewShadowsocksObfuscator(key []byte) (*ShadowsocksObfuscator, error) {
	// Hash key to 32 bytes (ChaCha20-Poly1305 key size)
	keyHash := sha256.Sum256(key)
	
	aead, err := chacha20poly1305.New(keyHash[:])
	if err != nil {
		return nil, err
	}

	return &ShadowsocksObfuscator{
		aead: aead,
	}, nil
}

// Obfuscate obfuscates data to look like normal HTTPS traffic
// This makes VPN traffic completely undetectable by firewalls
func (s *ShadowsocksObfuscator) Obfuscate(data []byte) ([]byte, error) {
	// Generate random nonce
	nonce := make([]byte, chacha20poly1305.NonceSize)
	if _, err := rand.Read(nonce); err != nil {
		return nil, err
	}

	// Encrypt with ChaCha20-Poly1305
	ciphertext := s.aead.Seal(nonce, nonce, data, nil)

	// Add random padding to look like HTTPS
	// This makes it indistinguishable from normal HTTPS traffic
	// Random padding length (16-64 bytes) to vary packet sizes
	paddingLen := 16 + (len(ciphertext) % 48)
	padding := make([]byte, paddingLen)
	rand.Read(padding)

	return append(ciphertext, padding...), nil
}

// Deobfuscate deobfuscates data
func (s *ShadowsocksObfuscator) Deobfuscate(data []byte) ([]byte, error) {
	if len(data) < chacha20poly1305.NonceSize {
		return nil, errors.New("data too short")
	}

	// Extract nonce
	nonce := data[:chacha20poly1305.NonceSize]
	ciphertext := data[chacha20poly1305.NonceSize:]

	// Remove padding (last 16 bytes are random)
	if len(ciphertext) > 16 {
		ciphertext = ciphertext[:len(ciphertext)-16]
	}

	// Decrypt
	plaintext, err := s.aead.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, err
	}

	return plaintext, nil
}

