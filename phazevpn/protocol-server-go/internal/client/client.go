package client

import (
	"crypto/rand"
	"fmt"
	"log"
	"net"
	"sync"
	"time"

	"phazevpn-server/internal/crypto"
	"phazevpn-server/internal/protocol"
	"phazevpn-server/internal/tun"
)

// PhazeVPNClient represents the VPN client
type PhazeVPNClient struct {
	serverAddr string
	serverPort int
	vpnNetwork string
	clientIP   string

	conn      *net.UDPConn
	serverUDP *net.UDPAddr
	tun       *tun.Manager
	crypto    *crypto.Manager

	sessionID uint32
	sequence  uint32
	connected bool

	mu       sync.RWMutex
	stopChan chan struct{}

	// Stats
	bytesSent int64
	bytesRecv int64
}

// NewPhazeVPNClient creates a new VPN client
func NewPhazeVPNClient(serverAddr string, serverPort int, vpnNetwork string, clientIP string) (*PhazeVPNClient, error) {
	client := &PhazeVPNClient{
		serverAddr: serverAddr,
		serverPort: serverPort,
		vpnNetwork: vpnNetwork,
		clientIP:   clientIP,
		stopChan:   make(chan struct{}),
	}

	return client, nil
}

// Connect establishes connection to the VPN server
func (c *PhazeVPNClient) Connect() error {
	log.Println("🔌 Connecting to PhazeVPN server...")

	// Resolve server address
	serverAddr := fmt.Sprintf("%s:%d", c.serverAddr, c.serverPort)
	udpAddr, err := net.ResolveUDPAddr("udp", serverAddr)
	if err != nil {
		return fmt.Errorf("failed to resolve server address: %w", err)
	}
	c.serverUDP = udpAddr

	// Create UDP connection
	conn, err := net.ListenUDP("udp", nil)
	if err != nil {
		return fmt.Errorf("failed to create UDP socket: %w", err)
	}
	c.conn = conn

	// Initialize crypto
	var err2 error
	c.crypto, err2 = crypto.NewManager()
	if err2 != nil {
		c.conn.Close()
		return fmt.Errorf("failed to initialize crypto: %w", err2)
	}

	// Perform handshake
	if err := c.performHandshake(); err != nil {
		c.conn.Close()
		return fmt.Errorf("handshake failed: %w", err)
	}

	// Create TUN interface
	tunMgr, err := tun.NewManager("phaze0", c.clientIP)
	if err != nil {
		c.conn.Close()
		return fmt.Errorf("failed to create TUN interface: %w", err)
	}
	c.tun = tunMgr

	c.connected = true
	log.Println("✅ Connected to PhazeVPN server")

	// Start packet handlers
	go c.handleUDPPackets()
	go c.handleTUNPackets()
	go c.keepaliveLoop()

	return nil
}

// performHandshake performs the VPN handshake
func (c *PhazeVPNClient) performHandshake() error {
	log.Println("🤝 Performing handshake...")

	// Generate client key pair
	publicKey := make([]byte, 32)
	if _, err := rand.Read(publicKey); err != nil {
		return err
	}

	// Create client hello
	clientHello, err := protocol.NewClientHello(publicKey)
	if err != nil {
		return err
	}

	// Serialize handshake payload
	payload, err := clientHello.Serialize()
	if err != nil {
		return err
	}

	// Create handshake packet
	pkt := protocol.NewHandshakePacket(0, payload)

	// Send client hello
	data, err := pkt.Serialize()
	if err != nil {
		return err
	}

	if _, err := c.conn.WriteToUDP(data, c.serverUDP); err != nil {
		return err
	}

	log.Println("📤 Sent ClientHello")

	// Wait for server hello
	c.conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	buf := make([]byte, 2048)
	n, _, err := c.conn.ReadFromUDP(buf)
	if err != nil {
		return fmt.Errorf("timeout waiting for ServerHello: %w", err)
	}
	c.conn.SetReadDeadline(time.Time{})

	// Parse server hello
	serverPkt, err := protocol.ParsePacket(buf[:n])
	if err != nil {
		return err
	}

	if serverPkt.Type != protocol.PacketTypeHandshake {
		return fmt.Errorf("unexpected packet type: %d", serverPkt.Type)
	}

	serverHello, err := protocol.ParseHandshakePayload(serverPkt.Payload)
	if err != nil {
		return err
	}

	if serverHello.Type != protocol.HandshakeTypeServerHello {
		return fmt.Errorf("unexpected handshake type: %d", serverHello.Type)
	}

	log.Println("📥 Received ServerHello")

	// Store session ID
	c.sessionID = serverPkt.SessionID

	// Send client finish
	clientFinish, err := protocol.NewClientFinish()
	if err != nil {
		return err
	}

	finishPayload, err := clientFinish.Serialize()
	if err != nil {
		return err
	}

	finishPkt := protocol.NewHandshakePacket(c.sessionID, finishPayload)
	finishData, err := finishPkt.Serialize()
	if err != nil {
		return err
	}

	if _, err := c.conn.WriteToUDP(finishData, c.serverUDP); err != nil {
		return err
	}

	log.Println("✅ Handshake complete - Session ID:", c.sessionID)

	return nil
}

// handleUDPPackets handles incoming UDP packets from server
func (c *PhazeVPNClient) handleUDPPackets() {
	buf := make([]byte, 65536)

	for {
		select {
		case <-c.stopChan:
			return
		default:
		}

		c.conn.SetReadDeadline(time.Now().Add(1 * time.Second))
		n, _, err := c.conn.ReadFromUDP(buf)
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				continue
			}
			log.Printf("UDP read error: %v", err)
			continue
		}

		// Parse packet
		pkt, err := protocol.ParsePacket(buf[:n])
		if err != nil {
			log.Printf("Failed to parse packet: %v", err)
			continue
		}

		// Handle packet
		switch pkt.Type {
		case protocol.PacketTypeData:
			c.handleDataPacket(pkt)
		case protocol.PacketTypeKeepalive:
			// Server is alive
		case protocol.PacketTypeError:
			log.Printf("Server error: %s", string(pkt.Payload))
		}

		c.bytesRecv += int64(n)
	}
}

// handleDataPacket handles data packets
func (c *PhazeVPNClient) handleDataPacket(pkt *protocol.Packet) {
	// Decrypt payload
	decrypted, err := c.crypto.Decrypt(pkt.Payload, pkt.SessionID)
	if err != nil {
		log.Printf("Failed to decrypt packet: %v", err)
		return
	}

	// Write to TUN
	if _, err := c.tun.Write(decrypted); err != nil {
		log.Printf("Failed to write to TUN: %v", err)
	}
}

// handleTUNPackets handles packets from TUN interface
func (c *PhazeVPNClient) handleTUNPackets() {
	buf := make([]byte, 2048)

	for {
		select {
		case <-c.stopChan:
			return
		default:
		}

		n, err := c.tun.Read(buf)
		if err != nil {
			log.Printf("TUN read error: %v", err)
			continue
		}

		// Encrypt data
		encrypted, err := c.crypto.Encrypt(buf[:n], c.sessionID)
		if err != nil {
			log.Printf("Failed to encrypt: %v", err)
			continue
		}

		// Create data packet
		c.mu.Lock()
		c.sequence++
		seq := c.sequence
		c.mu.Unlock()

		pkt := protocol.NewDataPacket(c.sessionID, encrypted)
		pkt.Sequence = seq

		// Send to server
		data, err := pkt.Serialize()
		if err != nil {
			log.Printf("Failed to serialize packet: %v", err)
			continue
		}

		if _, err := c.conn.WriteToUDP(data, c.serverUDP); err != nil {
			log.Printf("Failed to send packet: %v", err)
			continue
		}

		c.bytesSent += int64(len(data))
	}
}

// keepaliveLoop sends periodic keepalive packets
func (c *PhazeVPNClient) keepaliveLoop() {
	ticker := time.NewTicker(25 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-c.stopChan:
			return
		case <-ticker.C:
			pkt := protocol.NewKeepalivePacket(c.sessionID)
			data, err := pkt.Serialize()
			if err != nil {
				continue
			}

			c.conn.WriteToUDP(data, c.serverUDP)
		}
	}
}

// Disconnect closes the VPN connection
func (c *PhazeVPNClient) Disconnect() error {
	log.Println("🔌 Disconnecting from PhazeVPN...")

	c.mu.Lock()
	if !c.connected {
		c.mu.Unlock()
		return nil
	}
	c.connected = false
	c.mu.Unlock()

	close(c.stopChan)

	if c.tun != nil {
		c.tun.Close()
	}

	if c.conn != nil {
		c.conn.Close()
	}

	log.Println("✅ Disconnected")
	return nil
}

// GetStats returns connection statistics
func (c *PhazeVPNClient) GetStats() (sent, recv int64) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.bytesSent, c.bytesRecv
}

// IsConnected returns connection status
func (c *PhazeVPNClient) IsConnected() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.connected
}
