package tun

import (
	"github.com/songgao/water"
)

// Manager manages the TUN interface
type Manager struct {
	iface *water.Interface
	name  string
	ip    string
}

// Read reads from the TUN interface
func (m *Manager) Read(buf []byte) (int, error) {
	return m.iface.Read(buf)
}

// Write writes to the TUN interface
func (m *Manager) Write(buf []byte) (int, error) {
	return m.iface.Write(buf)
}

// Close closes the TUN interface
func (m *Manager) Close() error {
	if m.iface != nil {
		return m.iface.Close()
	}
	return nil
}

// Name returns the interface name
func (m *Manager) Name() string {
	return m.name
}

// IP returns the interface IP
func (m *Manager) IP() string {
	return m.ip
}
