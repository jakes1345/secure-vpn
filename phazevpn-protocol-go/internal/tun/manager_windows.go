package tun

import (
	"fmt"
	"os/exec"

	"github.com/songgao/water"
)

// NewManager creates a new TUN manager for Windows
func NewManager(name, ip string) (*Manager, error) {
	config := water.Config{
		DeviceType: water.TUN,
		PlatformSpecificParams: water.PlatformSpecificParams{
			ComponentID: "tap0901",
			Network:     name,
		},
	}

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

// Create creates and configures the TUN interface for Windows
func (m *Manager) Create() error {
	// Set IP address using netsh
	// This assumes the interface name is recognized by Windows networking stack
	cmd := exec.Command("netsh", "interface", "ip", "set", "address", m.name, "static", m.ip, "255.255.255.0")
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to set IP address: %v, output: %s", err, out)
	}

	return nil
}
