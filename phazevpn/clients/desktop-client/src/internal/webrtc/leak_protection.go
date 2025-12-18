package webrtc

import (
	"log"
	"os/exec"
)

// WebRTCProtection manages WebRTC leak protection
type WebRTCProtection struct {
	enabled bool
}

// NewWebRTCProtection creates a new WebRTC protection manager
func NewWebRTCProtection() *WebRTCProtection {
	return &WebRTCProtection{
		enabled: false,
	}
}

// Enable blocks WebRTC STUN/TURN to prevent IP leaks
func (w *WebRTCProtection) Enable() error {
	log.Println("🔒 Blocking WebRTC to prevent IP leaks...")

	rules := [][]string{
		// Block STUN (Session Traversal Utilities for NAT)
		{"iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "3478", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "3478", "-j", "REJECT"},

		// Block TURN (Traversal Using Relays around NAT)
		{"iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "3479", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "3479", "-j", "REJECT"},

		// Block alternative STUN/TURN ports
		{"iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "5349", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "5349", "-j", "REJECT"},

		// Block common WebRTC ports (19302-19309)
		{"iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "19302:19309", "-j", "REJECT"},

		// Block Google STUN servers (most common)
		{"iptables", "-A", "OUTPUT", "-d", "stun.l.google.com", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-d", "stun1.l.google.com", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-d", "stun2.l.google.com", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-d", "stun3.l.google.com", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-d", "stun4.l.google.com", "-j", "REJECT"},

		// Block other common STUN servers
		{"iptables", "-A", "OUTPUT", "-d", "stun.stunprotocol.org", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-d", "stun.voip.blackberry.com", "-j", "REJECT"},
	}

	for _, rule := range rules {
		cmd := exec.Command(rule[0], rule[1:]...)
		if err := cmd.Run(); err != nil {
			log.Printf("⚠️  Failed to add WebRTC blocking rule: %v", err)
			// Continue with other rules
		}
	}

	w.enabled = true
	log.Println("✅ WebRTC blocked - no IP leaks via WebRTC")
	return nil
}

// Disable removes WebRTC blocking rules
func (w *WebRTCProtection) Disable() error {
	if !w.enabled {
		return nil
	}

	log.Println("🔓 Removing WebRTC blocks...")

	rules := [][]string{
		{"iptables", "-D", "OUTPUT", "-p", "udp", "--dport", "3478", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "3478", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "udp", "--dport", "3479", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "3479", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "udp", "--dport", "5349", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "5349", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "udp", "--dport", "19302:19309", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-d", "stun.l.google.com", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-d", "stun1.l.google.com", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-d", "stun2.l.google.com", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-d", "stun3.l.google.com", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-d", "stun4.l.google.com", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-d", "stun.stunprotocol.org", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-d", "stun.voip.blackberry.com", "-j", "REJECT"},
	}

	for _, rule := range rules {
		cmd := exec.Command(rule[0], rule[1:]...)
		cmd.Run() // Ignore errors on cleanup
	}

	w.enabled = false
	log.Println("✅ WebRTC blocks removed")
	return nil
}

// IsEnabled returns whether WebRTC protection is enabled
func (w *WebRTCProtection) IsEnabled() bool {
	return w.enabled
}
