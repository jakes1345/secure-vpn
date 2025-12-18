package server

import (
	"fmt"
	"sync"
	"time"
)

// ReplayProtection prevents replay attacks
type ReplayProtection struct {
	seenSequences map[uint32]time.Time
	maxSequence   uint32
	windowSize    uint32
	mu            sync.RWMutex
	cleanupTicker *time.Ticker
}

// NewReplayProtection creates a new replay protection instance
func NewReplayProtection(windowSize uint32) *ReplayProtection {
	rp := &ReplayProtection{
		seenSequences: make(map[uint32]time.Time),
		windowSize:    windowSize,
	}

	// Cleanup old sequences every minute
	rp.cleanupTicker = time.NewTicker(1 * time.Minute)
	go rp.cleanup()

	return rp
}

// CheckAndAdd checks if a sequence number was already seen
func (rp *ReplayProtection) CheckAndAdd(sequence uint32) bool {
	rp.mu.Lock()
	defer rp.mu.Unlock()

	// Check if too old (outside window)
	if sequence < rp.maxSequence-rp.windowSize {
		return false // Too old, reject
	}

	// Check if already seen
	if _, seen := rp.seenSequences[sequence]; seen {
		return false // Replay attack, reject
	}

	// Add to seen set
	rp.seenSequences[sequence] = time.Now()
	if sequence > rp.maxSequence {
		rp.maxSequence = sequence
	}

	return true // New packet, accept
}

// cleanup removes old sequences outside the window
func (rp *ReplayProtection) cleanup() {
	for range rp.cleanupTicker.C {
		rp.mu.Lock()
		cutoff := rp.maxSequence - rp.windowSize
		for seq := range rp.seenSequences {
			if seq < cutoff {
				delete(rp.seenSequences, seq)
			}
		}
		rp.mu.Unlock()
	}
}

// IPPool manages IP address assignment
type IPPool struct {
	network    string
	serverIP   string
	nextIP     uint32
	assigned   map[string]uint32 // client IP -> session ID
	reverse    map[uint32]string  // session ID -> client IP
	mu         sync.RWMutex
}

// NewIPPool creates a new IP pool
func NewIPPool(network, serverIP string) *IPPool {
	return &IPPool{
		network:  network,
		serverIP: serverIP,
		nextIP:   2, // Start from .2 (server is .1)
		assigned: make(map[string]uint32),
		reverse:  make(map[uint32]string),
	}
}

// AssignIP assigns an IP address to a session
func (p *IPPool) AssignIP(sessionID uint32) string {
	p.mu.Lock()
	defer p.mu.Unlock()

	// Check if already assigned
	if ip, exists := p.reverse[sessionID]; exists {
		return ip
	}

	// Find next available IP
	for {
		ip := fmt.Sprintf("10.9.0.%d", p.nextIP)
		if _, assigned := p.assigned[ip]; !assigned {
			p.assigned[ip] = sessionID
			p.reverse[sessionID] = ip
			p.nextIP++
			if p.nextIP > 254 {
				p.nextIP = 2 // Wrap around
			}
			return ip
		}
		p.nextIP++
		if p.nextIP > 254 {
			p.nextIP = 2
		}
	}
}

// ReleaseIP releases an IP address
func (p *IPPool) ReleaseIP(sessionID uint32) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if ip, exists := p.reverse[sessionID]; exists {
		delete(p.assigned, ip)
		delete(p.reverse, sessionID)
	}
}

// GetIP returns the IP for a session
func (p *IPPool) GetIP(sessionID uint32) (string, bool) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	ip, exists := p.reverse[sessionID]
	return ip, exists
}

// GetSessionID returns the session ID for an IP
func (p *IPPool) GetSessionID(ip string) (uint32, bool) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	sessionID, exists := p.assigned[ip]
	return sessionID, exists
}

// RoutingTable manages packet routing
type RoutingTable struct {
	routes map[string]uint32 // destination IP -> session ID
	mu     sync.RWMutex
}

// NewRoutingTable creates a new routing table
func NewRoutingTable() *RoutingTable {
	return &RoutingTable{
		routes: make(map[string]uint32),
	}
}

// AddRoute adds a route
func (rt *RoutingTable) AddRoute(destIP string, sessionID uint32) {
	rt.mu.Lock()
	defer rt.mu.Unlock()
	rt.routes[destIP] = sessionID
}

// RemoveRoute removes a route
func (rt *RoutingTable) RemoveRoute(destIP string) {
	rt.mu.Lock()
	defer rt.mu.Unlock()
	delete(rt.routes, destIP)
}

// GetRoute returns the session ID for a destination IP
func (rt *RoutingTable) GetRoute(destIP string) (uint32, bool) {
	rt.mu.RLock()
	defer rt.mu.RUnlock()
	sessionID, exists := rt.routes[destIP]
	return sessionID, exists
}

// extractDestIP extracts destination IP from IP packet
func extractDestIP(packet []byte) (string, error) {
	if len(packet) < 20 {
		return "", fmt.Errorf("packet too short")
	}

	// Check IP version (first 4 bits)
	version := (packet[0] >> 4) & 0x0F
	if version != 4 {
		return "", fmt.Errorf("not IPv4")
	}

	// Extract destination IP (bytes 16-19)
	destIP := fmt.Sprintf("%d.%d.%d.%d",
		packet[16], packet[17], packet[18], packet[19])

	return destIP, nil
}

