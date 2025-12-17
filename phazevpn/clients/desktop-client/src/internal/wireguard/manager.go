package wireguard

import (
	"fmt"
	"os/exec"
	"strings"
)

// Manager handles WireGuard integration
type Manager struct {
	interfaceName string
	configPath    string
}

// NewManager creates a new WireGuard manager
func NewManager(interfaceName, configPath string) *Manager {
	return &Manager{
		interfaceName: interfaceName,
		configPath:    configPath,
	}
}

// IsInstalled checks if WireGuard is installed
func (m *Manager) IsInstalled() bool {
	_, err := exec.LookPath("wg")
	return err == nil
}

// Install installs WireGuard (requires root)
func (m *Manager) Install() error {
	// Try different package managers
	commands := [][]string{
		{"apt-get", "update", "&&", "apt-get", "install", "-y", "wireguard"},
		{"yum", "install", "-y", "wireguard-tools"},
		{"dnf", "install", "-y", "wireguard-tools"},
	}

	for _, cmd := range commands {
		parts := strings.Split(cmd[0], " ")
		if err := exec.Command(parts[0], parts[1:]...).Run(); err == nil {
			return nil
		}
	}

	return fmt.Errorf("failed to install WireGuard: no package manager found")
}

// CreateInterface creates a WireGuard interface
func (m *Manager) CreateInterface() error {
	// Check if interface already exists
	if m.InterfaceExists() {
		return nil
	}

	cmd := exec.Command("ip", "link", "add", "dev", m.interfaceName, "type", "wireguard")
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to create WireGuard interface: %w", err)
	}

	return nil
}

// InterfaceExists checks if the interface exists
func (m *Manager) InterfaceExists() bool {
	cmd := exec.Command("ip", "link", "show", m.interfaceName)
	return cmd.Run() == nil
}

// Configure configures WireGuard with a config file
func (m *Manager) Configure(configPath string) error {
	cmd := exec.Command("wg", "setconf", m.interfaceName, configPath)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to configure WireGuard: %w", err)
	}
	return nil
}

// Up brings the interface up
func (m *Manager) Up() error {
	cmd := exec.Command("ip", "link", "set", m.interfaceName, "up")
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to bring interface up: %w", err)
	}
	return nil
}

// Down brings the interface down
func (m *Manager) Down() error {
	cmd := exec.Command("ip", "link", "set", m.interfaceName, "down")
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to bring interface down: %w", err)
	}
	return nil
}

// DeleteInterface deletes the WireGuard interface
func (m *Manager) DeleteInterface() error {
	if !m.InterfaceExists() {
		return nil
	}

	m.Down()

	cmd := exec.Command("ip", "link", "delete", m.interfaceName)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to delete interface: %w", err)
	}
	return nil
}

// GenerateKeyPair generates a WireGuard key pair
func GenerateKeyPair() (privateKey, publicKey string, err error) {
	// Generate private key
	privateCmd := exec.Command("wg", "genkey")
	privateKeyBytes, err := privateCmd.Output()
	if err != nil {
		return "", "", fmt.Errorf("failed to generate private key: %w", err)
	}
	privateKey = strings.TrimSpace(string(privateKeyBytes))

	// Generate public key from private key
	publicCmd := exec.Command("wg", "pubkey")
	publicCmd.Stdin = strings.NewReader(privateKey)
	publicKeyBytes, err := publicCmd.Output()
	if err != nil {
		return "", "", fmt.Errorf("failed to generate public key: %w", err)
	}
	publicKey = strings.TrimSpace(string(publicKeyBytes))

	return privateKey, publicKey, nil
}

// GenerateConfig generates a WireGuard server config
func GenerateConfig(interfaceName, privateKey, address, listenPort string, peers []Peer) string {
	config := fmt.Sprintf("[Interface]\n")
	config += fmt.Sprintf("PrivateKey = %s\n", privateKey)
	config += fmt.Sprintf("Address = %s\n", address)
	config += fmt.Sprintf("ListenPort = %s\n", listenPort)
	config += fmt.Sprintf("PostUp = iptables -A FORWARD -i %s -j ACCEPT; iptables -A FORWARD -o %s -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n", interfaceName, interfaceName)
	config += fmt.Sprintf("PostDown = iptables -D FORWARD -i %s -j ACCEPT; iptables -D FORWARD -o %s -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n", interfaceName, interfaceName)
	config += "\n"

	for _, peer := range peers {
		config += fmt.Sprintf("[Peer]\n")
		config += fmt.Sprintf("PublicKey = %s\n", peer.PublicKey)
		if peer.AllowedIPs != "" {
			config += fmt.Sprintf("AllowedIPs = %s\n", peer.AllowedIPs)
		}
		if peer.Endpoint != "" {
			config += fmt.Sprintf("Endpoint = %s\n", peer.Endpoint)
		}
		config += "\n"
	}

	return config
}

// Peer represents a WireGuard peer
type Peer struct {
	PublicKey  string
	AllowedIPs string
	Endpoint   string
}

