package protocol

import (
	"crypto/rand"
	"encoding/binary"
	"errors"
	"time"
)

// Handshake packet types
const (
	HandshakeTypeClientHello  = 0x01
	HandshakeTypeServerHello  = 0x02
	HandshakeTypeClientFinish = 0x03
	HandshakeTypeServerFinish = 0x04
)

// HandshakePayload represents a handshake packet payload
type HandshakePayload struct {
	Type         uint8
	PublicKey    []byte // 32 bytes for Curve25519
	Nonce        []byte // 24 bytes
	Timestamp    uint64
	ProtocolVer  uint8
	CipherSuites []uint8
}

// ParseHandshakePayload parses a handshake payload
func ParseHandshakePayload(data []byte) (*HandshakePayload, error) {
	if len(data) < 66 { // 1 + 32 + 24 + 8 + 1
		return nil, errors.New("handshake payload too short")
	}

	payload := &HandshakePayload{}
	offset := 0

	// Type (1 byte)
	payload.Type = data[offset]
	offset++

	// Public Key (32 bytes)
	payload.PublicKey = make([]byte, 32)
	copy(payload.PublicKey, data[offset:offset+32])
	offset += 32

	// Nonce (24 bytes)
	payload.Nonce = make([]byte, 24)
	copy(payload.Nonce, data[offset:offset+24])
	offset += 24

	// Timestamp (8 bytes)
	payload.Timestamp = binary.BigEndian.Uint64(data[offset : offset+8])
	offset += 8

	// Protocol Version (1 byte)
	payload.ProtocolVer = data[offset]
	offset++

	// Cipher Suites (remaining bytes)
	if len(data) > offset {
		payload.CipherSuites = data[offset:]
	}

	return payload, nil
}

// Serialize converts handshake payload to bytes
func (h *HandshakePayload) Serialize() ([]byte, error) {
	size := 1 + 32 + 24 + 8 + 1 + len(h.CipherSuites)
	buf := make([]byte, size)
	offset := 0

	// Type
	buf[offset] = h.Type
	offset++

	// Public Key
	copy(buf[offset:], h.PublicKey)
	offset += 32

	// Nonce
	copy(buf[offset:], h.Nonce)
	offset += 24

	// Timestamp
	binary.BigEndian.PutUint64(buf[offset:], h.Timestamp)
	offset += 8

	// Protocol Version
	buf[offset] = h.ProtocolVer
	offset++

	// Cipher Suites
	copy(buf[offset:], h.CipherSuites)

	return buf, nil
}

// NewClientHello creates a client hello handshake
func NewClientHello(publicKey []byte) (*HandshakePayload, error) {
	if len(publicKey) != 32 {
		return nil, errors.New("invalid public key length")
	}

	nonce := make([]byte, 24)
	if _, err := rand.Read(nonce); err != nil {
		return nil, err
	}

	return &HandshakePayload{
		Type:         HandshakeTypeClientHello,
		PublicKey:    publicKey,
		Nonce:        nonce,
		Timestamp:    uint64(time.Now().Unix()),
		ProtocolVer:  ProtocolVersion,
		CipherSuites: []uint8{0x01}, // ChaCha20-Poly1305
	}, nil
}

// NewServerHello creates a server hello handshake
func NewServerHello(publicKey []byte, clientNonce []byte) (*HandshakePayload, error) {
	if len(publicKey) != 32 {
		return nil, errors.New("invalid public key length")
	}

	// Use client nonce + server random
	nonce := make([]byte, 24)
	copy(nonce[:12], clientNonce[:12])
	if _, err := rand.Read(nonce[12:]); err != nil {
		return nil, err
	}

	return &HandshakePayload{
		Type:         HandshakeTypeServerHello,
		PublicKey:    publicKey,
		Nonce:        nonce,
		Timestamp:    uint64(time.Now().Unix()),
		ProtocolVer:  ProtocolVersion,
		CipherSuites: []uint8{0x01}, // ChaCha20-Poly1305
	}, nil
}

// NewClientFinish creates a client finish handshake
func NewClientFinish() (*HandshakePayload, error) {
	nonce := make([]byte, 24)
	if _, err := rand.Read(nonce); err != nil {
		return nil, err
	}

	return &HandshakePayload{
		Type:        HandshakeTypeClientFinish,
		PublicKey:   make([]byte, 32), // Placeholder
		Nonce:       nonce,
		Timestamp:   uint64(time.Now().Unix()),
		ProtocolVer: ProtocolVersion,
	}, nil
}

// NewServerFinish creates a server finish handshake
func NewServerFinish() (*HandshakePayload, error) {
	nonce := make([]byte, 24)
	if _, err := rand.Read(nonce); err != nil {
		return nil, err
	}

	return &HandshakePayload{
		Type:        HandshakeTypeServerFinish,
		PublicKey:   make([]byte, 32), // Placeholder
		Nonce:       nonce,
		Timestamp:   uint64(time.Now().Unix()),
		ProtocolVer: ProtocolVersion,
	}, nil
}
