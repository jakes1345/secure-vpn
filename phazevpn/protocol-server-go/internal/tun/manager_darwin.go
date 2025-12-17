package tun

import (
	"fmt"
	"os/exec"

	"github.com/songgao/water"
)

// NewManager creates a new TUN manager for macOS
func NewManager(name, ip string) (*Manager, error) {
	config := water.Config{
		DeviceType: water.TUN,
	}

	iface, err := water.New(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create TUN interface: %w", err)
	}

	return &Manager{
		iface: iface,
		name:  iface.Name(), // macOS assigns names like utun0, utun1...
		ip:    ip,
	}, nil
}

// Create creates and configures the TUN interface for macOS
func (m *Manager) Create() error {
	// Point-to-point address setup for macOS
	// syntax: ifconfig <interface> <local_address> <remote_address> up
	cmd := exec.Command("ifconfig", m.name, m.ip, m.ip, "up")
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to set IP address: %v, output: %s", err, out)
	}

	return nil
}
