package security

import (
	"log"
	"sync"
	"time"
)

// AbusePrevention prevents VPN abuse - SIMPLE BUT EFFECTIVE
type AbusePrevention struct {
	// Simple rate limiting (connections per minute)
	connectionAttempts map[string][]time.Time
	rateMu            sync.RWMutex
	
	// Active connections per IP
	connectionsPerIP map[string]int
	connMu           sync.RWMutex
	
	// Banned IPs (simple map)
	bannedIPs map[string]time.Time
	banMu     sync.RWMutex
	
	// Traffic tracking (bytes per second per IP)
	trafficPerIP map[string]*TrafficCounter
	trafficMu    sync.RWMutex
	
	// Config - OPTIMIZED FOR 4K GAMING & STREAMING
	maxConnectionsPerIP int      // Max 3 connections per IP (prevents botnets)
	maxConnPerMinute    int      // Max 5 connection attempts per minute
	maxBytesPerSecond   int64    // Max 200Mbps (25MB/s) per IP - supports 4K streaming + gaming
	premiumBytesPerSecond int64  // Premium users: 500Mbps (62.5MB/s) - unlimited 4K
	banDuration         time.Duration // Ban for 1 hour
	
	// Premium/whitelisted users (for 4K gaming/streaming)
	premiumIPs map[string]bool
	premiumMu sync.RWMutex
	
	// Stats
	blockedCount int64
	allowedCount int64
}

// TrafficCounter tracks traffic per IP
type TrafficCounter struct {
	Bytes     int64
	LastReset time.Time
}


// NewAbusePrevention creates a simple but effective abuse prevention system
// OPTIMIZED FOR 4K GAMING & STREAMING
func NewAbusePrevention() *AbusePrevention {
	ap := &AbusePrevention{
		connectionAttempts: make(map[string][]time.Time),
		connectionsPerIP:   make(map[string]int),
		bannedIPs:          make(map[string]time.Time),
		trafficPerIP:       make(map[string]*TrafficCounter),
		premiumIPs:         make(map[string]bool),
		maxConnectionsPerIP: 3,  // Max 3 connections per IP (stops botnets)
		maxConnPerMinute:    5,  // Max 5 connection attempts per minute
		maxBytesPerSecond:   25 * 1024 * 1024, // 200Mbps (25MB/s) - supports 4K streaming + gaming
		premiumBytesPerSecond: 62 * 1024 * 1024, // 500Mbps (62.5MB/s) - unlimited 4K for premium
		banDuration:         1 * time.Hour,    // Ban for 1 hour
	}
	
	// Cleanup old bans every 5 minutes
	go ap.cleanupBans()
	
	return ap
}

// CheckConnection checks if a connection should be allowed - SIMPLE AND EFFECTIVE
func (ap *AbusePrevention) CheckConnection(ip string) bool {
	// 1. Check if banned
	if ap.isBanned(ip) {
		ap.blockedCount++
		return false
	}
	
	// 2. Check connection rate (max 5 attempts per minute)
	if !ap.checkRateLimit(ip) {
		ap.blockedCount++
		ap.banIP(ip) // Auto-ban if rate limit exceeded
		return false
	}
	
	// 3. Check max connections per IP (max 3 - prevents botnets)
	if ap.getConnections(ip) >= ap.maxConnectionsPerIP {
		ap.blockedCount++
		return false
	}
	
	// All checks passed
	ap.allowedCount++
	return true
}

// RecordConnection records a new connection
func (ap *AbusePrevention) RecordConnection(ip string) {
	ap.connMu.Lock()
	defer ap.connMu.Unlock()
	ap.connectionsPerIP[ip]++
}

// RemoveConnection removes a connection
func (ap *AbusePrevention) RemoveConnection(ip string) {
	ap.connMu.Lock()
	defer ap.connMu.Unlock()
	if count := ap.connectionsPerIP[ip]; count > 0 {
		ap.connectionsPerIP[ip]--
		if ap.connectionsPerIP[ip] == 0 {
			delete(ap.connectionsPerIP, ip)
		}
	}
}

// RecordTraffic records traffic and checks for abuse
// OPTIMIZED FOR 4K GAMING & STREAMING
func (ap *AbusePrevention) RecordTraffic(ip string, bytes int64) {
	ap.trafficMu.Lock()
	defer ap.trafficMu.Unlock()
	
	counter, exists := ap.trafficPerIP[ip]
	if !exists {
		counter = &TrafficCounter{
			Bytes:     0,
			LastReset: time.Now(),
		}
		ap.trafficPerIP[ip] = counter
	}
	
	// Reset counter every second
	if time.Since(counter.LastReset) > 1*time.Second {
		counter.Bytes = 0
		counter.LastReset = time.Now()
	}
	
	counter.Bytes += bytes
	
	// Check if premium user (higher limits for 4K gaming/streaming)
	isPremium := ap.isPremium(ip)
	maxBytes := ap.maxBytesPerSecond
	if isPremium {
		maxBytes = ap.premiumBytesPerSecond
	}
	
	// Check if exceeding max bytes per second (DDoS detection)
	if counter.Bytes > maxBytes {
		log.Printf("🚫 High traffic from %s: %d bytes/sec (max: %d, premium: %v)", 
			ip, counter.Bytes, maxBytes, isPremium)
		// Only ban if way over limit (2x) - allows burst for 4K
		if counter.Bytes > maxBytes*2 {
			ap.banIP(ip)
		}
	}
}

// Helper functions - SIMPLE AND EFFECTIVE

// isBanned checks if IP is banned
func (ap *AbusePrevention) isBanned(ip string) bool {
	ap.banMu.RLock()
	defer ap.banMu.RUnlock()
	
	banTime, exists := ap.bannedIPs[ip]
	if !exists {
		return false
	}
	
	// Check if ban expired
	if time.Now().After(banTime) {
		return false
	}
	
	return true
}

// banIP bans an IP address
func (ap *AbusePrevention) banIP(ip string) {
	ap.banMu.Lock()
	defer ap.banMu.Unlock()
	ap.bannedIPs[ip] = time.Now().Add(ap.banDuration)
	log.Printf("🚫 Banned IP %s for %v", ip, ap.banDuration)
}

// checkRateLimit checks connection rate (max 5 per minute)
func (ap *AbusePrevention) checkRateLimit(ip string) bool {
	ap.rateMu.Lock()
	defer ap.rateMu.Unlock()
	
	now := time.Now()
	cutoff := now.Add(-1 * time.Minute)
	
	// Get attempts for this IP
	attempts := ap.connectionAttempts[ip]
	
	// Remove old attempts
	validAttempts := make([]time.Time, 0)
	for _, attempt := range attempts {
		if attempt.After(cutoff) {
			validAttempts = append(validAttempts, attempt)
		}
	}
	
	// Check limit
	if len(validAttempts) >= ap.maxConnPerMinute {
		return false
	}
	
	// Record new attempt
	validAttempts = append(validAttempts, now)
	ap.connectionAttempts[ip] = validAttempts
	
	return true
}

// getConnections gets connection count for IP
func (ap *AbusePrevention) getConnections(ip string) int {
	ap.connMu.RLock()
	defer ap.connMu.RUnlock()
	return ap.connectionsPerIP[ip]
}

// cleanupBans removes expired bans
func (ap *AbusePrevention) cleanupBans() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()
	
	for range ticker.C {
		ap.banMu.Lock()
		now := time.Now()
		for ip, banTime := range ap.bannedIPs {
			if now.After(banTime) {
				delete(ap.bannedIPs, ip)
			}
		}
		ap.banMu.Unlock()
	}
}

// AddPremiumIP adds an IP to premium list (for 4K gaming/streaming)
func (ap *AbusePrevention) AddPremiumIP(ip string) {
	ap.premiumMu.Lock()
	defer ap.premiumMu.Unlock()
	ap.premiumIPs[ip] = true
	log.Printf("⭐ Premium access granted to %s (4K gaming/streaming enabled)", ip)
}

// RemovePremiumIP removes premium access
func (ap *AbusePrevention) RemovePremiumIP(ip string) {
	ap.premiumMu.Lock()
	defer ap.premiumMu.Unlock()
	delete(ap.premiumIPs, ip)
}

// isPremium checks if IP has premium access
func (ap *AbusePrevention) isPremium(ip string) bool {
	ap.premiumMu.RLock()
	defer ap.premiumMu.RUnlock()
	return ap.premiumIPs[ip]
}

// GetStats returns simple stats
func (ap *AbusePrevention) GetStats() map[string]interface{} {
	ap.banMu.RLock()
	bannedCount := len(ap.bannedIPs)
	ap.banMu.RUnlock()
	
	ap.connMu.RLock()
	activeConnections := len(ap.connectionsPerIP)
	ap.connMu.RUnlock()
	
	ap.premiumMu.RLock()
	premiumCount := len(ap.premiumIPs)
	ap.premiumMu.RUnlock()
	
	return map[string]interface{}{
		"blocked":           ap.blockedCount,
		"allowed":           ap.allowedCount,
		"banned_ips":        bannedCount,
		"active_connections": activeConnections,
		"premium_users":     premiumCount,
		"max_bandwidth_mbps": ap.maxBytesPerSecond * 8 / (1024 * 1024), // Convert to Mbps
		"premium_bandwidth_mbps": ap.premiumBytesPerSecond * 8 / (1024 * 1024),
	}
}

