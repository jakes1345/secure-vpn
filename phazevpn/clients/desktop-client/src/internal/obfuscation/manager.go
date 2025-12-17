package obfuscation

import (
	"errors"
	"sync"
)

// Manager handles multiple obfuscation layers
type Manager struct {
	shadowsocks *ShadowsocksObfuscator
	v2ray       *V2RayObfuscator
	enabled     map[string]bool
	mu          sync.RWMutex
}

// NewManager creates a new obfuscation manager
func NewManager(shadowsocksKey []byte, v2rayURL string) (*Manager, error) {
	mgr := &Manager{
		enabled: make(map[string]bool),
	}

	// Initialize Shadowsocks
	if shadowsocksKey != nil {
		ss, err := NewShadowsocksObfuscator(shadowsocksKey)
		if err != nil {
			return nil, err
		}
		mgr.shadowsocks = ss
		mgr.enabled["shadowsocks"] = true
	}

	// Initialize V2Ray (optional)
	if v2rayURL != "" {
		v2ray, err := NewV2RayObfuscator(v2rayURL, nil)
		if err != nil {
			return nil, err
		}
		mgr.v2ray = v2ray
		mgr.enabled["v2ray"] = true
	}

	return mgr, nil
}

// Obfuscate applies all enabled obfuscation layers
func (m *Manager) Obfuscate(data []byte) ([]byte, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var err error
	result := data

	// Apply Shadowsocks first (base obfuscation)
	if m.enabled["shadowsocks"] && m.shadowsocks != nil {
		result, err = m.shadowsocks.Obfuscate(result)
		if err != nil {
			return nil, err
		}
	}

	// Apply V2Ray (WebSocket + TLS obfuscation)
	if m.enabled["v2ray"] && m.v2ray != nil {
		result, err = m.v2ray.ObfuscateData(result)
		if err != nil {
			return nil, err
		}
	}

	return result, nil
}

// Deobfuscate removes all obfuscation layers (reverse order)
func (m *Manager) Deobfuscate(data []byte) ([]byte, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var err error
	result := data

	// Remove V2Ray first (last applied)
	if m.enabled["v2ray"] && m.v2ray != nil {
		result, err = m.v2ray.DeobfuscateData(result)
		if err != nil {
			return nil, err
		}
	}

	// Remove Shadowsocks (first applied)
	if m.enabled["shadowsocks"] && m.shadowsocks != nil {
		result, err = m.shadowsocks.Deobfuscate(result)
		if err != nil {
			return nil, err
		}
	}

	return result, nil
}

// Enable enables an obfuscation layer
func (m *Manager) Enable(layer string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	switch layer {
	case "shadowsocks":
		if m.shadowsocks == nil {
			return errors.New("Shadowsocks not initialized")
		}
		m.enabled["shadowsocks"] = true
	case "v2ray":
		if m.v2ray == nil {
			return errors.New("V2Ray not initialized")
		}
		m.enabled["v2ray"] = true
	default:
		return errors.New("unknown obfuscation layer")
	}

	return nil
}

// Disable disables an obfuscation layer
func (m *Manager) Disable(layer string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.enabled, layer)
}

// IsEnabled checks if a layer is enabled
func (m *Manager) IsEnabled(layer string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.enabled[layer]
}

