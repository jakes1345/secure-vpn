package server

import (
	"crypto/rand"
	"errors"
	"fmt"

	"golang.org/x/crypto/curve25519"
)

// KeyExchange handles X25519 key exchange
type KeyExchange struct {
	privateKey [32]byte
	publicKey  [32]byte
}

// NewKeyExchange creates a new key exchange instance
func NewKeyExchange() (*KeyExchange, error) {
	kx := &KeyExchange{}

	// Generate private key
	if _, err := rand.Read(kx.privateKey[:]); err != nil {
		return nil, fmt.Errorf("failed to generate private key: %w", err)
	}

	// Compute public key
	curve25519.ScalarBaseMult(&kx.publicKey, &kx.privateKey)

	return kx, nil
}

// GetPublicKey returns the public key
func (kx *KeyExchange) GetPublicKey() [32]byte {
	return kx.publicKey
}

// ComputeSharedSecret computes the shared secret with a peer's public key
func (kx *KeyExchange) ComputeSharedSecret(peerPublicKey [32]byte) ([32]byte, error) {
	var sharedSecret [32]byte
	curve25519.ScalarMult(&sharedSecret, &kx.privateKey, &peerPublicKey)
	return sharedSecret, nil
}

// PerformKeyExchange performs a key exchange with a client
func (s *PhazeVPNServer) performKeyExchange(clientPublicKey []byte) ([]byte, error) {
	if len(clientPublicKey) != 32 {
		return nil, errors.New("invalid public key length")
	}

	var peerKey [32]byte
	copy(peerKey[:], clientPublicKey)

	// Create key exchange
	kx, err := NewKeyExchange()
	if err != nil {
		return nil, err
	}

	// Compute shared secret (for future key derivation)
	_, err = kx.ComputeSharedSecret(peerKey)
	if err != nil {
		return nil, err
	}

	// Return server's public key
	// In production, would derive session keys from shared secret
	publicKey := kx.GetPublicKey()
	return publicKey[:], nil
}

