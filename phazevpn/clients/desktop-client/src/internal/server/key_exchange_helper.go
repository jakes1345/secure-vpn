package server

import (
	"crypto/rand"
	"fmt"

	"golang.org/x/crypto/curve25519"
)

// KeyExchange handles X25519 key exchange
type KeyExchange struct {
	privateKey [32]byte
	publicKey  [32]byte
}

// NewKeyExchange creates a new key exchange instance
func NewKeyExchange() *KeyExchange {
	kx := &KeyExchange{}

	// Generate private key
	if _, err := rand.Read(kx.privateKey[:]); err != nil {
		// In a real app we might panic or return error, but here we just log?
		// Since generic return type in server.go didn't expect error, we will assume generic init for now or panic
		panic(fmt.Errorf("failed to generate private key: %w", err))
	}

	// Compute public key
	curve25519.ScalarBaseMult(&kx.publicKey, &kx.privateKey)

	return kx
}

// GetPublicKey returns the public key
func (kx *KeyExchange) GetPublicKey() [32]byte {
	return kx.publicKey
}

// ComputeSharedSecret computes the shared secret with peer's public key
func (kx *KeyExchange) ComputeSharedSecret(peerPublicKey []byte) ([32]byte, error) {
	var sharedSecret [32]byte
	var peerKey [32]byte
	
	if len(peerPublicKey) != 32 {
		return sharedSecret, fmt.Errorf("invalid peer public key length: %d", len(peerPublicKey))
	}
	copy(peerKey[:], peerPublicKey)

	curve25519.ScalarMult(&sharedSecret, &kx.privateKey, &peerKey)
	return sharedSecret, nil
}
