package protocol

import (
	"encoding/binary"
	"errors"
)

const (
	// Protocol version
	ProtocolVersion = 1

	// Magic number: "PHAZ"
	MagicNumber = 0x5048415A

	// Packet types
	PacketTypeHandshake = 0x01
	PacketTypeData      = 0x02
	PacketTypeKeepalive = 0x03
	PacketTypeError     = 0xFF
)

// Packet represents a PhazeVPN protocol packet
type Packet struct {
	Magic     uint32
	Version   uint8
	Type      uint8
	Sequence  uint32
	SessionID uint32
	Length    uint16
	Payload   []byte
}

// ParsePacket parses a raw packet from bytes
func ParsePacket(data []byte) (*Packet, error) {
	if len(data) < 16 {
		return nil, errors.New("packet too short")
	}

	pkt := &Packet{}

	// Parse header (16 bytes)
	pkt.Magic = binary.BigEndian.Uint32(data[0:4])
	if pkt.Magic != MagicNumber {
		return nil, errors.New("invalid magic number")
	}

	pkt.Version = data[4]
	pkt.Type = data[5]
	pkt.Sequence = binary.BigEndian.Uint32(data[6:10])
	pkt.SessionID = binary.BigEndian.Uint32(data[10:14])
	pkt.Length = binary.BigEndian.Uint16(data[14:16])

	// Parse payload
	if len(data) < 16+int(pkt.Length) {
		return nil, errors.New("packet payload incomplete")
	}

	pkt.Payload = make([]byte, pkt.Length)
	copy(pkt.Payload, data[16:16+int(pkt.Length)])

	return pkt, nil
}

// Serialize converts a packet to bytes
func (p *Packet) Serialize() ([]byte, error) {
	if len(p.Payload) > 0xFFFF {
		return nil, errors.New("payload too large")
	}

	p.Length = uint16(len(p.Payload))

	buf := make([]byte, 16+len(p.Payload))

	// Write header
	binary.BigEndian.PutUint32(buf[0:4], p.Magic)
	buf[4] = p.Version
	buf[5] = p.Type
	binary.BigEndian.PutUint32(buf[6:10], p.Sequence)
	binary.BigEndian.PutUint32(buf[10:14], p.SessionID)
	binary.BigEndian.PutUint16(buf[14:16], p.Length)

	// Write payload
	copy(buf[16:], p.Payload)

	return buf, nil
}

// NewHandshakePacket creates a new handshake packet
func NewHandshakePacket(sessionID uint32, payload []byte) *Packet {
	return &Packet{
		Magic:     MagicNumber,
		Version:   ProtocolVersion,
		Type:      PacketTypeHandshake,
		Sequence:  0,
		SessionID: sessionID,
		Payload:   payload,
	}
}

// NewDataPacket creates a new data packet
func NewDataPacket(sessionID uint32, payload []byte) *Packet {
	return &Packet{
		Magic:     MagicNumber,
		Version:   ProtocolVersion,
		Type:      PacketTypeData,
		Sequence:  0, // Would be incremented in real implementation
		SessionID: sessionID,
		Payload:   payload,
	}
}

// NewKeepalivePacket creates a new keepalive packet
func NewKeepalivePacket(sessionID uint32) *Packet {
	return &Packet{
		Magic:     MagicNumber,
		Version:   ProtocolVersion,
		Type:      PacketTypeKeepalive,
		Sequence:  0,
		SessionID: sessionID,
		Payload:   nil,
	}
}

