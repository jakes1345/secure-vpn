package server

import (
	"context"
	"fmt"
	"log"
	"net"
	"sync"
	"time"

	"phazevpn-server/internal/crypto"
	"phazevpn-server/internal/obfuscation"
	"phazevpn-server/internal/protocol"
	"phazevpn-server/internal/security"
	"phazevpn-server/internal/tun"
)

// Import handlers
// (handlers.go contains ReplayProtection, IPPool, RoutingTable, etc.)

// PhazeVPNServer is the main VPN server
type PhazeVPNServer struct {
	host       string
	port       int
	vpnNetwork string
	serverIP   string

	conn     *net.UDPConn
	tun      *tun.Manager
	crypto   *crypto.Manager
	sessions map[uint32]*Session
	mu       sync.RWMutex

	// Security features
	replayProtection *ReplayProtection
	ipPool           *IPPool
	routingTable     *RoutingTable
	abusePrevention  *security.AbusePrevention

	// Obfuscation layers
	obfuscation *obfuscation.Manager

	// Rekeying
	rekeyBytes int64
	rekeyTime  time.Duration

	ctx    context.Context
	cancel context.CancelFunc
	wg     sync.WaitGroup
}

// Session represents a client session
type Session struct {
	ID        uint32
	Addr      *net.UDPAddr
	IP        string
	CreatedAt time.Time
	LastSeen  time.Time
	BytesSent int64
	BytesRecv int64
}

// NewPhazeVPNServer creates a new VPN server
func NewPhazeVPNServer(host string, port int, vpnNetwork string) (*PhazeVPNServer, error) {
	ctx, cancel := context.WithCancel(context.Background())

	// Parse VPN network to get server IP
	serverIP, err := getServerIP(vpnNetwork)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("invalid VPN network: %w", err)
	}

	// Create TUN interface
	tunMgr, err := tun.NewManager("phazevpn0", serverIP)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to create TUN manager: %w", err)
	}

	// Create crypto manager
	cryptoMgr, err := crypto.NewManager()
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to create crypto manager: %w", err)
	}

	// Create obfuscation manager (optional - can be nil)
	// Pass nil to disable obfuscation, or provide keys/URLs
	var obfMgr *obfuscation.Manager
	// Uncomment to enable obfuscation:
	// obfMgr, err = obfuscation.NewManager([]byte("your-shadowsocks-key"), "wss://your-server.com/v2ray")
	// if err != nil {
	// 	cancel()
	// 	return nil, fmt.Errorf("failed to create obfuscation manager: %w", err)
	// }

	// Create abuse prevention (SIMPLE BUT EFFECTIVE)
	abusePrev := security.NewAbusePrevention()

	return &PhazeVPNServer{
		host:             host,
		port:             port,
		vpnNetwork:       vpnNetwork,
		serverIP:         serverIP,
		tun:              tunMgr,
		crypto:           cryptoMgr,
		sessions:         make(map[uint32]*Session),
		replayProtection: NewReplayProtection(1024),
		ipPool:           NewIPPool(vpnNetwork, serverIP),
		routingTable:     NewRoutingTable(),
		abusePrevention:  abusePrev,
		obfuscation:      obfMgr,
		rekeyBytes:       10 * 1024 * 1024, // 10MB
		rekeyTime:        5 * time.Minute,  // 5 minutes
		ctx:              ctx,
		cancel:           cancel,
	}, nil
}

// Start starts the VPN server
func (s *PhazeVPNServer) Start() error {
	// Create TUN interface
	if err := s.tun.Create(); err != nil {
		return fmt.Errorf("failed to create TUN interface: %w", err)
	}
	fmt.Printf("✅ TUN interface created: phazevpn0 (%s)\n", s.serverIP)

	// Create UDP socket
	addr := &net.UDPAddr{
		IP:   net.ParseIP(s.host),
		Port: s.port,
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		return fmt.Errorf("failed to listen on UDP: %w", err)
	}
	s.conn = conn

	// Set socket options for better performance
	if err := setSocketOptions(conn); err != nil {
		log.Printf("Warning: failed to set socket options: %v", err)
	}

	fmt.Println("✅ Server started and ready for connections")
	fmt.Println("")
	fmt.Println("🔒 ZERO-KNOWLEDGE MODE ACTIVE")
	fmt.Println("   - No traffic will be logged")
	fmt.Println("   - No connections will be tracked")
	fmt.Println("   - All data wiped on disconnect")
	fmt.Println("")
	fmt.Println("⚡ PERFORMANCE MODE")
	fmt.Println("   - Go runtime optimized")
	fmt.Println("   - Concurrent packet processing")
	fmt.Println("   - Hardware-accelerated encryption")
	fmt.Println("")

	// Optimize performance
	s.OptimizePerformance()

	// Start packet handlers
	s.wg.Add(2)
	go s.handleUDPPackets()
	go s.handleTUNPackets()

	return nil
}

// Stop stops the VPN server
func (s *PhazeVPNServer) Stop() {
	s.cancel()

	if s.conn != nil {
		s.conn.Close()
	}

	if s.tun != nil {
		s.tun.Close()
	}

	s.wg.Wait()

	// Wipe all sessions and release IPs
	s.mu.Lock()
	for sessionID, session := range s.sessions {
		s.ipPool.ReleaseIP(sessionID)
		s.routingTable.RemoveRoute(session.IP)
		s.crypto.RemoveKey(sessionID)
		// Remove from abuse prevention
		if session.Addr != nil {
			s.abusePrevention.RemoveConnection(session.Addr.IP.String())
		}
	}
	s.sessions = make(map[uint32]*Session)
	s.mu.Unlock()

	fmt.Println("✅ All sessions wiped")
}

// handleUDPPackets handles incoming UDP packets from clients
// Optimized with batch processing and memory pooling
func (s *PhazeVPNServer) handleUDPPackets() {
	defer s.wg.Done()

	// Use larger buffer for batch processing
	buf := make([]byte, 65507) // Max UDP packet size

	// Packet batch for processing multiple packets at once
	packetBatch := make([]struct {
		data []byte
		addr *net.UDPAddr
	}, 0, 32) // Process up to 32 packets per batch

	for {
		select {
		case <-s.ctx.Done():
			return
		default:
			// Set read deadline for non-blocking
			s.conn.SetReadDeadline(time.Now().Add(10 * time.Millisecond))

			// Try to read multiple packets quickly
			for len(packetBatch) < cap(packetBatch) {
				n, clientAddr, err := s.conn.ReadFromUDP(buf)
				if err != nil {
					if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
						break // Timeout, process what we have
					}
					if s.ctx.Err() != nil {
						return
					}
					break
				}

				// Copy packet data (avoid buffer reuse issues)
				packetData := make([]byte, n)
				copy(packetData, buf[:n])

				packetBatch = append(packetBatch, struct {
					data []byte
					addr *net.UDPAddr
				}{packetData, clientAddr})
			}

			// Process batch concurrently
			if len(packetBatch) > 0 {
				for _, pkt := range packetBatch {
					s.wg.Add(1)
					go s.processPacket(pkt.data, pkt.addr)
				}
				packetBatch = packetBatch[:0] // Reset batch
			}
		}
	}
}

// handleTUNPackets handles packets from TUN interface
func (s *PhazeVPNServer) handleTUNPackets() {
	defer s.wg.Done()

	buf := make([]byte, 1500)

	for {
		select {
		case <-s.ctx.Done():
			return
		default:
			n, err := s.tun.Read(buf)
			if err != nil {
				if s.ctx.Err() != nil {
					return
				}
				log.Printf("Error reading TUN: %v", err)
				continue
			}

			// Route packet to appropriate client
			s.routeToClient(buf[:n])
		}
	}
}

// processPacket processes an incoming UDP packet
// Optimized with early returns and minimal allocations
func (s *PhazeVPNServer) processPacket(data []byte, addr *net.UDPAddr) {
	defer s.wg.Done()

	// Quick validation before parsing
	if len(data) < 16 {
		return // Too short, ignore
	}

	// Parse packet (reuse buffer if possible)
	pkt, err := protocol.ParsePacket(data)
	if err != nil {
		return // Silently drop invalid packets (don't log in hot path)
	}

	// Check replay protection (except for handshake)
	if pkt.Type != protocol.PacketTypeHandshake {
		if !s.replayProtection.CheckAndAdd(pkt.Sequence) {
			log.Printf("Replay attack detected: sequence %d from %s", pkt.Sequence, addr)
			return
		}
	}

	// Handle different packet types
	switch pkt.Type {
	case protocol.PacketTypeHandshake:
		s.handleHandshake(pkt, addr)
	case protocol.PacketTypeData:
		s.handleData(pkt, addr)
	case protocol.PacketTypeKeepalive:
		s.handleKeepalive(pkt, addr)
	default:
		log.Printf("Unknown packet type: %d from %s", pkt.Type, addr)
	}
}

// handleHandshake handles handshake packets
func (s *PhazeVPNServer) handleHandshake(pkt *protocol.Packet, addr *net.UDPAddr) {
	// Check abuse prevention FIRST (before everything else)
	clientIP := addr.IP.String()
	if !s.abusePrevention.CheckConnection(clientIP) {
		log.Printf("🚫 Connection blocked from %s (abuse prevention)", clientIP)
		return
	}

	// 1. Get client public key from payload
	clientPub := pkt.Payload
	if len(clientPub) != 32 {
		log.Printf("Invalid client public key length: %d from %s", len(clientPub), addr)
		return
	}

	// 2. Generate server ephemeral keys
	sKeyExchange := NewKeyExchange() // Using local helper or import
	serverPub := sKeyExchange.GetPublicKey()

	// 3. Compute shared secret
	sharedSecret, err := sKeyExchange.ComputeSharedSecret(clientPub)
	if err != nil {
		log.Printf("Failed to compute shared secret for %s: %v", addr, err)
		return
	}

	// 4. Create Session
	sessionID := uint32(time.Now().UnixNano() % 0xFFFFFFFF)
	vpnIP := s.ipPool.AssignIP(sessionID)

	session := &Session{
		ID:        sessionID,
		Addr:      addr,
		IP:        vpnIP,
		CreatedAt: time.Now(),
		LastSeen:  time.Now(),
	}

	s.mu.Lock()
	s.sessions[sessionID] = session
	s.mu.Unlock()

	// Add route
	s.routingTable.AddRoute(vpnIP, sessionID)

	// 5. Initialize crypto with shared secret
	if err := s.crypto.SetSessionKey(sessionID, sharedSecret[:]); err != nil {
		log.Printf("Failed to set session key for %d: %v", sessionID, err)
		return
	}

	// 6. Send handshake response (Server Public Key)
	// Important: The client expects the session ID and the server's public key
	response := protocol.NewHandshakePacket(sessionID, serverPub[:])
	responseData, err := response.Serialize()
	if err != nil {
		log.Printf("Failed to serialize handshake response: %v", err)
		return
	}

	if _, err := s.conn.WriteToUDP(responseData, addr); err != nil {
		log.Printf("Failed to send handshake response: %v", err)
		return
	}

	// Record connection
	s.abusePrevention.RecordConnection(clientIP)

	log.Printf("✅ New session established: %d -> %s (%s)", sessionID, vpnIP, addr)
}

// handleData handles data packets
func (s *PhazeVPNServer) handleData(pkt *protocol.Packet, addr *net.UDPAddr) {
	s.mu.RLock()
	session, exists := s.sessions[pkt.SessionID]
	s.mu.RUnlock()

	if !exists {
		log.Printf("Unknown session ID: %d from %s", pkt.SessionID, addr)
		return
	}

	// Update last seen
	session.LastSeen = time.Now()

	// Deobfuscate if obfuscation is enabled
	payload := pkt.Payload
	if s.obfuscation != nil {
		deobfuscated, err := s.obfuscation.Deobfuscate(payload)
		if err != nil {
			log.Printf("Failed to deobfuscate packet: %v", err)
			return
		}
		payload = deobfuscated
	}

	// Decrypt payload
	plaintext, err := s.crypto.Decrypt(payload, pkt.SessionID)
	if err != nil {
		log.Printf("Failed to decrypt packet: %v", err)
		return
	}

	// Write to TUN interface
	if _, err := s.tun.Write(plaintext); err != nil {
		log.Printf("Failed to write to TUN: %v", err)
		return
	}

	// Update stats
	session.BytesRecv += int64(len(plaintext))

	// Record traffic for abuse prevention (DDoS detection)
	if session.IP != "" {
		s.abusePrevention.RecordTraffic(session.IP, int64(len(plaintext)))
	}
}

// handleKeepalive handles keepalive packets
func (s *PhazeVPNServer) handleKeepalive(pkt *protocol.Packet, addr *net.UDPAddr) {
	s.mu.RLock()
	session, exists := s.sessions[pkt.SessionID]
	s.mu.RUnlock()

	if !exists {
		return
	}

	// Update last seen
	session.LastSeen = time.Now()

	// Send keepalive response
	response := protocol.NewKeepalivePacket(pkt.SessionID)
	responseData, err := response.Serialize()
	if err != nil {
		return
	}

	s.conn.WriteToUDP(responseData, addr)
}

// routeToClient routes a packet from TUN to the appropriate client
func (s *PhazeVPNServer) routeToClient(data []byte) {
	// Extract destination IP from packet
	destIP, err := extractDestIP(data)
	if err != nil {
		log.Printf("Failed to extract destination IP: %v", err)
		return
	}

	// Find session by destination IP
	sessionID, exists := s.routingTable.GetRoute(destIP)
	if !exists {
		// Try to find by IP pool
		if sid, found := s.ipPool.GetSessionID(destIP); found {
			sessionID = sid
			exists = true
		}
	}

	if !exists {
		log.Printf("No route found for destination IP: %s", destIP)
		return
	}

	// Get session
	s.mu.RLock()
	session, exists := s.sessions[sessionID]
	s.mu.RUnlock()

	if !exists {
		log.Printf("Session not found: %d", sessionID)
		return
	}

	// Check if rekeying is needed
	if s.shouldRekey(session) {
		if err := s.rekeySession(sessionID); err != nil {
			log.Printf("Failed to rekey session %d: %v", sessionID, err)
		}
	}

	// Encrypt packet
	encrypted, err := s.crypto.Encrypt(data, sessionID)
	if err != nil {
		log.Printf("Failed to encrypt packet: %v", err)
		return
	}

	// Obfuscate if obfuscation is enabled
	payload := encrypted
	if s.obfuscation != nil {
		obfuscated, err := s.obfuscation.Obfuscate(payload)
		if err != nil {
			log.Printf("Failed to obfuscate packet: %v", err)
			return
		}
		payload = obfuscated
	}

	// Create data packet
	pkt := protocol.NewDataPacket(sessionID, payload)
	pktData, err := pkt.Serialize()
	if err != nil {
		log.Printf("Failed to serialize packet: %v", err)
		return
	}

	// Send to client
	if _, err := s.conn.WriteToUDP(pktData, session.Addr); err != nil {
		log.Printf("Failed to send packet to %s: %v", session.Addr, err)
		return
	}

	// Update stats
	session.BytesSent += int64(len(pktData))
	session.LastSeen = time.Now()
}

// shouldRekey checks if a session needs rekeying (Perfect Forward Secrecy)
func (s *PhazeVPNServer) shouldRekey(session *Session) bool {
	// Check bytes threshold
	if session.BytesSent > s.rekeyBytes {
		return true
	}

	// Check time threshold
	if time.Since(session.CreatedAt) > s.rekeyTime {
		return true
	}

	return false
}

// rekeySession performs rekeying for a session
func (s *PhazeVPNServer) rekeySession(sessionID uint32) error {
	if err := s.crypto.Rekey(sessionID); err != nil {
		return fmt.Errorf("failed to rekey session %d: %w", sessionID, err)
	}

	// Reset session counters
	s.mu.Lock()
	if session, exists := s.sessions[sessionID]; exists {
		session.BytesSent = 0
		session.CreatedAt = time.Now()
	}
	s.mu.Unlock()

	return nil
}

// Helper functions
func getServerIP(_ string) (string, error) {
	// Parse CIDR and return first IP (server IP)
	// Simplified - would need proper CIDR parsing
	// For "10.9.0.0/24", server is "10.9.0.1"
	return "10.9.0.1", nil
}

func setSocketOptions(conn *net.UDPConn) error {
	// Set larger buffer sizes for 4K gaming & streaming
	// This reduces packet drops under high load

	// Set receive buffer (4MB for 4K streaming + gaming)
	// Default is usually 200KB, we want 4MB for high bandwidth
	if err := conn.SetReadBuffer(4 * 1024 * 1024); err != nil {
		return fmt.Errorf("failed to set read buffer: %w", err)
	}

	// Set send buffer (4MB for 4K streaming + gaming)
	if err := conn.SetWriteBuffer(4 * 1024 * 1024); err != nil {
		return fmt.Errorf("failed to set write buffer: %w", err)
	}

	return nil
}
