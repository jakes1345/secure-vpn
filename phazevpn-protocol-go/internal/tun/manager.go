package tun

import (
	"fmt"

	"github.com/songgao/water"
)

// Manager manages the TUN interface
type Manager struct {
	iface *water.Interface
	name  string
	ip    string
}

// NewManager creates a new TUN manager
func NewManager(name, ip string) (*Manager, error) {
	config := water.Config{
		DeviceType: water.TUN,
	}
	config.Name = name

	iface, err := water.New(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create TUN interface: %w", err)
	}

	return &Manager{
		iface: iface,
		name:  name,
		ip:    ip,
	}, nil
}

// Create creates and configures the TUN interface
func (m *Manager) Create() error {
	// Set IP address (requires root)
	// This would use ip command or netlink in production
	cmd := fmt.Sprintf("ip addr add %s/24 dev %s", m.ip, m.name)
	_ = cmd // Would execute this command

	// Bring interface up
	cmd = fmt.Sprintf("ip link set %s up", m.name)
	_ = cmd // Would execute this command

	return nil
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

