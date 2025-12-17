package tun

import (
	"fmt"
	"os/exec"

	"github.com/songgao/water"
)

// NewManager creates a new TUN manager for Linux
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

// Create creates and configures the TUN interface for Linux
func (m *Manager) Create() error {
	// Set IP address (requires root)
	cmd := exec.Command("ip", "addr", "add", m.ip+"/24", "dev", m.name)
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to set IP address: %v, output: %s", err, out)
	}

	// Bring interface up
	cmd = exec.Command("ip", "link", "set", m.name, "up")
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to bring interface up: %v, output: %s", err, out)
	}

	return nil
}
