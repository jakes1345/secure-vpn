package server

import (
	"crypto/rand"
	"encoding/binary"
	"sync"
	"time"
)

// SessionManager manages client sessions
type SessionManager struct {
	sessions map[uint32]*Session
	mu       sync.RWMutex
	timeout  time.Duration
}

// NewSessionManager creates a new session manager
func NewSessionManager(timeout time.Duration) *SessionManager {
	sm := &SessionManager{
		sessions: make(map[uint32]*Session),
		timeout:  timeout,
	}

	// Start cleanup goroutine
	go sm.cleanupLoop()

	return sm
}

// CreateSession creates a new session
func (sm *SessionManager) CreateSession(clientAddr string, clientPubKey []byte) (*Session, error) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Generate session ID
	sessionID := sm.generateSessionID()

	// Create session
	session := &Session{
		ID:        sessionID,
		Addr:      nil, // Will be set when we have UDPAddr
		IP:        clientAddr,
		CreatedAt: time.Now(),
		LastSeen:  time.Now(),
		BytesSent: 0,
		BytesRecv: 0,
	}

	sm.sessions[sessionID] = session

	return session, nil
}

// GetSession retrieves a session by ID
func (sm *SessionManager) GetSession(sessionID uint32) (*Session, bool) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	session, exists := sm.sessions[sessionID]
	return session, exists
}

// UpdateSession updates session last seen time
func (sm *SessionManager) UpdateSession(sessionID uint32) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if session, exists := sm.sessions[sessionID]; exists {
		session.LastSeen = time.Now()
	}
}

// RemoveSession removes a session
func (sm *SessionManager) RemoveSession(sessionID uint32) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	delete(sm.sessions, sessionID)
}

// GetAllSessions returns all active sessions
func (sm *SessionManager) GetAllSessions() []*Session {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	sessions := make([]*Session, 0, len(sm.sessions))
	for _, session := range sm.sessions {
		sessions = append(sessions, session)
	}

	return sessions
}

// CleanupExpired removes expired sessions
func (sm *SessionManager) CleanupExpired() int {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	now := time.Now()
	removed := 0

	for id, session := range sm.sessions {
		if now.Sub(session.LastSeen) > sm.timeout {
			delete(sm.sessions, id)
			removed++
		}
	}

	return removed
}

// cleanupLoop periodically cleans up expired sessions
func (sm *SessionManager) cleanupLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		removed := sm.CleanupExpired()
		if removed > 0 {
			// Log cleanup
		}
	}
}

// generateSessionID generates a random session ID
func (sm *SessionManager) generateSessionID() uint32 {
	var id uint32

	// Keep generating until we get a unique ID
	for {
		b := make([]byte, 4)
		rand.Read(b)
		id = binary.BigEndian.Uint32(b)

		// Check if ID already exists
		if _, exists := sm.sessions[id]; !exists {
			break
		}
	}

	return id
}

// Session represents an extended session with more fields
type SessionExt struct {
	*Session
	ClientPubKey []byte
	ServerPubKey []byte
	SharedSecret []byte
	Active       bool
}
