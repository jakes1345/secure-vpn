package models

import (
	"secure-vpn/web-portal/config"
	"secure-vpn/web-portal/utils"
	"os"
	"path/filepath"
	"fmt"
)

// Client represents a VPN client device.
type Client struct {
	ID           string `json:"id"`
	Name         string `json:"name"`
	Protocol     string `json:"protocol"` // openvpn, wireguard, phazevpn
	ConfigPath   string `json:"config_path"`
	IsActive     bool   `json:"is_active"`
	LastActivity string `json:"last_activity"`
}

// GetClientConfigPath returns the absolute path to the client's configuration file.
func GetClientConfigPath(username, clientID, protocol string) string {
	cfg := config.GetConfig()
	// Example path: /opt/phaze-vpn/client-configs/john/client_12345.ovpn
	
	// Determine file extension
	ext := ""
	switch protocol {
	case "openvpn":
		ext = ".ovpn"
	case "wireguard":
		ext = ".conf"
	case "phazevpn":
		ext = ".phaze"
	default:
		ext = ".conf"
	}

	// Create a user-specific subdirectory for organization
	userDir := filepath.Join(cfg.ClientConfigsDir, username)
	
	// Ensure the user-specific directory exists
	os.MkdirAll(userDir, 0755)

	filename := fmt.Sprintf("client_%s%s", clientID, ext)
	return filepath.Join(userDir, filename)
}

// GenerateClientConfig is a placeholder for the actual config generation logic.
// In a real application, this would call out to a VPN management system (e.g., Easy-RSA, WireGuard tools).
func GenerateClientConfig(username, clientID, protocol string) (string, error) {
	// --- Placeholder Logic ---
	configPath := GetClientConfigPath(username, clientID, protocol)
	
	// Simulate config generation content
	content := fmt.Sprintf(
		"# SecureVPN Client Config\n" +
		"# User: %s\n" +
		"# Client ID: %s\n" +
		"# Protocol: %s\n" +
		"remote %s %d\n" +
		"ca /etc/openvpn/ca.crt\n" +
		"cert /etc/openvpn/client/%s.crt\n" +
		"key /etc/openvpn/client/%s.key\n",
		username, clientID, protocol, config.GetConfig().VpnServerIP, config.GetConfig().VpnServerPort, username, username,
	)
	
	// Write the config file
	err := os.WriteFile(configPath, []byte(content), 0644)
	if err != nil {
		return "", fmt.Errorf("failed to write config file: %w", err)
	}
	
	return configPath, nil
}

// GetClientConfig reads the client configuration file.
func GetClientConfig(username, clientID, protocol string) ([]byte, error) {
	configPath := GetClientConfigPath(username, clientID, protocol)
	
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		// If config doesn't exist, try to generate it
		_, err := GenerateClientConfig(username, clientID, protocol)
		if err != nil {
			return nil, fmt.Errorf("config not found and generation failed: %w", err)
		}
	}
	
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}
	
	return data, nil
}

// GenerateClientID generates a unique client ID.
func GenerateClientID() string {
	// Use a simple UUID-like string for now
	token, _ := utils.GenerateToken(8) // 8 bytes -> 11 base64 chars
	return token
}
