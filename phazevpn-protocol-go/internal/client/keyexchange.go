package client

import (
	"crypto/rand"
	"fmt"

	"golang.org/x/crypto/curve25519"
)

// KeyExchange handles X25519 key exchange for client
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

// ComputeSharedSecret computes the shared secret with server's public key
func (kx *KeyExchange) ComputeSharedSecret(serverPublicKey []byte) ([32]byte, error) {
	var sharedSecret [32]byte
	var serverKey [32]byte
	
	if len(serverPublicKey) != 32 {
		return sharedSecret, fmt.Errorf("invalid server public key length: %d", len(serverPublicKey))
	}
	copy(serverKey[:], serverPublicKey)

	curve25519.ScalarMult(&sharedSecret, &kx.privateKey, &serverKey)
	return sharedSecret, nil
}
