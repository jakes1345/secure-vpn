package crypto

import (
	"crypto/cipher"
	"crypto/rand"
	"errors"
	"sync"

	"golang.org/x/crypto/chacha20poly1305"
)

// Manager handles encryption/decryption
type Manager struct {
	// Per-session keys
	sessionKeys map[uint32]cipher.AEAD
	mu          sync.RWMutex
}

// NewManager creates a new crypto manager
func NewManager() (*Manager, error) {
	return &Manager{
		sessionKeys: make(map[uint32]cipher.AEAD),
	}, nil
}

// GetOrCreateKey gets or creates a key for a session
func (m *Manager) GetOrCreateKey(sessionID uint32) (cipher.AEAD, error) {
	m.mu.RLock()
	aead, exists := m.sessionKeys[sessionID]
	m.mu.RUnlock()

	if exists {
		return aead, nil
	}

	// Generate new key for this session
	key := make([]byte, chacha20poly1305.KeySize)
	if _, err := rand.Read(key); err != nil {
		return nil, err
	}

	aead, err := chacha20poly1305.New(key)
	if err != nil {
		return nil, err
	}

	m.mu.Lock()
	m.sessionKeys[sessionID] = aead
	m.mu.Unlock()

	return aead, nil
}

// SetSessionKey sets the encryption key for a session using a derived shared secret
func (m *Manager) SetSessionKey(sessionID uint32, key []byte) error {
	if len(key) != chacha20poly1305.KeySize {
		return errors.New("invalid key size")
	}

	aead, err := chacha20poly1305.New(key)
	if err != nil {
		return err
	}

	m.mu.Lock()
	m.sessionKeys[sessionID] = aead
	m.mu.Unlock()

	return nil
}

// Rekey generates a new key for a session (Perfect Forward Secrecy)
func (m *Manager) Rekey(sessionID uint32) error {
	key := make([]byte, chacha20poly1305.KeySize)
	if _, err := rand.Read(key); err != nil {
		return err
	}

	aead, err := chacha20poly1305.New(key)
	if err != nil {
		return err
	}

	m.mu.Lock()
	m.sessionKeys[sessionID] = aead
	m.mu.Unlock()

	return nil
}

// RemoveKey removes a session key (on disconnect)
func (m *Manager) RemoveKey(sessionID uint32) {
	m.mu.Lock()
	delete(m.sessionKeys, sessionID)
	m.mu.Unlock()
}

// Encrypt encrypts data for a session
func (m *Manager) Encrypt(plaintext []byte, sessionID uint32) ([]byte, error) {
	aead, err := m.GetOrCreateKey(sessionID)
	if err != nil {
		return nil, err
	}

	// Generate nonce
	nonce := make([]byte, chacha20poly1305.NonceSize)
	if _, err := rand.Read(nonce); err != nil {
		return nil, err
	}

	// Encrypt
	ciphertext := aead.Seal(nonce, nonce, plaintext, nil)
	return ciphertext, nil
}

// Decrypt decrypts data for a session
func (m *Manager) Decrypt(ciphertext []byte, sessionID uint32) ([]byte, error) {
	if len(ciphertext) < chacha20poly1305.NonceSize {
		return nil, errors.New("ciphertext too short")
	}

	aead, err := m.GetOrCreateKey(sessionID)
	if err != nil {
		return nil, err
	}

	// Extract nonce
	nonce := ciphertext[:chacha20poly1305.NonceSize]
	ciphertext = ciphertext[chacha20poly1305.NonceSize:]

	// Decrypt
	plaintext, err := aead.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, err
	}

	return plaintext, nil
}

