package obfuscation

import (
	"crypto/tls"
	"errors"
	"net"
	"net/http"
	"net/url"
	"time"

	"github.com/gorilla/websocket"
)

// V2RayObfuscator provides WebSocket + TLS obfuscation (looks like HTTPS)
type V2RayObfuscator struct {
	wsURL    string
	tlsConfig *tls.Config
	dialer   *websocket.Dialer
}

// NewV2RayObfuscator creates a new V2Ray obfuscator
func NewV2RayObfuscator(wsURL string, tlsConfig *tls.Config) (*V2RayObfuscator, error) {
	if wsURL == "" {
		return nil, errors.New("WebSocket URL required")
	}

	if tlsConfig == nil {
		tlsConfig = &tls.Config{
			InsecureSkipVerify: false,
			MinVersion:         tls.VersionTLS13,
		}
	}

	dialer := &websocket.Dialer{
		TLSClientConfig: tlsConfig,
		HandshakeTimeout: 10 * time.Second,
	}

	return &V2RayObfuscator{
		wsURL:     wsURL,
		tlsConfig: tlsConfig,
		dialer:    dialer,
	}, nil
}

// Connect establishes a WebSocket connection (looks like HTTPS)
func (v *V2RayObfuscator) Connect() (*websocket.Conn, error) {
	u, err := url.Parse(v.wsURL)
	if err != nil {
		return nil, err
	}

	// Add headers to make it look like a normal web request
	header := http.Header{}
	header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
	header.Set("Origin", "https://"+u.Host)
	header.Set("Sec-WebSocket-Protocol", "chat, superchat")

	conn, _, err := v.dialer.Dial(v.wsURL, header)
	if err != nil {
		return nil, err
	}

	return conn, nil
}

// Wrap wraps a connection with WebSocket + TLS
func (v *V2RayObfuscator) Wrap(conn net.Conn) (net.Conn, error) {
	// For server-side, we'd create a WebSocket server
	// This is a simplified version
	// Full implementation would use gorilla/websocket server
	
	// Convert net.Conn to WebSocket
	// This is a placeholder - full implementation would handle WebSocket upgrade
	return conn, nil
}

// ObfuscateData obfuscates data to look like WebSocket frames
func (v *V2RayObfuscator) ObfuscateData(data []byte) ([]byte, error) {
	// WebSocket frame format (simplified)
	// Full implementation would use proper WebSocket framing
	frame := make([]byte, 2+len(data))
	
	// FIN bit + opcode (binary)
	frame[0] = 0x82
	
	// Mask bit + payload length
	if len(data) < 126 {
		frame[1] = byte(len(data))
		copy(frame[2:], data)
		return frame[:2+len(data)], nil
	} else if len(data) < 65536 {
		frame[1] = 126
		frame[2] = byte(len(data) >> 8)
		frame[3] = byte(len(data))
		copy(frame[4:], data)
		return frame[:4+len(data)], nil
	}
	
	return nil, errors.New("payload too large")
}

// DeobfuscateData deobfuscates WebSocket frames
func (v *V2RayObfuscator) DeobfuscateData(data []byte) ([]byte, error) {
	if len(data) < 2 {
		return nil, errors.New("frame too short")
	}

	// Extract payload length
	payloadLen := int(data[1] & 0x7F)
	offset := 2

	if payloadLen == 126 {
		if len(data) < 4 {
			return nil, errors.New("frame incomplete")
		}
		payloadLen = int(data[2])<<8 | int(data[3])
		offset = 4
	} else if payloadLen == 127 {
		return nil, errors.New("64-bit length not supported")
	}

	if len(data) < offset+payloadLen {
		return nil, errors.New("payload incomplete")
	}

	return data[offset : offset+payloadLen], nil
}

