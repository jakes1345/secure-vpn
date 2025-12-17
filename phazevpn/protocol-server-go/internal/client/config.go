package client

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"os"
)

// Config represents a client configuration
type Config struct {
	ServerHost    string
	ServerPort    int
	ServerPublicKey string
	ClientPrivateKey string
	ClientPublicKey  string
	VPNNetwork    string
	ClientIP      string
}

// GenerateKeyPair generates a client key pair
func GenerateKeyPair() (privateKey, publicKey string, err error) {
	// Generate 32-byte private key
	privateKeyBytes := make([]byte, 32)
	if _, err := rand.Read(privateKeyBytes); err != nil {
		return "", "", err
	}
	
	// For now, use base64 encoding (in production, would use X25519)
	privateKey = base64.StdEncoding.EncodeToString(privateKeyBytes)
	
	// Generate public key (simplified - in production would use X25519)
	publicKeyBytes := make([]byte, 32)
	if _, err := rand.Read(publicKeyBytes); err != nil {
		return "", "", err
	}
	publicKey = base64.StdEncoding.EncodeToString(publicKeyBytes)
	
	return privateKey, publicKey, nil
}

// GenerateConfig generates a client configuration file
func GenerateConfig(serverHost string, serverPort int, serverPublicKey string, vpnNetwork string, clientIP string) (*Config, error) {
	// Generate client keys
	clientPrivateKey, clientPublicKey, err := GenerateKeyPair()
	if err != nil {
		return nil, fmt.Errorf("failed to generate client keys: %w", err)
	}
	
	return &Config{
		ServerHost:      serverHost,
		ServerPort:      serverPort,
		ServerPublicKey: serverPublicKey,
		ClientPrivateKey: clientPrivateKey,
		ClientPublicKey:  clientPublicKey,
		VPNNetwork:      vpnNetwork,
		ClientIP:        clientIP,
	}, nil
}

// Save saves the configuration to a file
func (c *Config) Save(filepath string) error {
	content := c.String()
	return os.WriteFile(filepath, []byte(content), 0600)
}

// String returns the configuration as a string (like WireGuard .conf format)
func (c *Config) String() string {
	config := "[PhazeVPN]\n"
	config += fmt.Sprintf("Server = %s:%d\n", c.ServerHost, c.ServerPort)
	config += fmt.Sprintf("ServerPublicKey = %s\n", c.ServerPublicKey)
	config += fmt.Sprintf("ClientPrivateKey = %s\n", c.ClientPrivateKey)
	config += fmt.Sprintf("ClientPublicKey = %s\n", c.ClientPublicKey)
	config += fmt.Sprintf("VPNNetwork = %s\n", c.VPNNetwork)
	config += fmt.Sprintf("ClientIP = %s\n", c.ClientIP)
	config += "\n"
	config += "# PhazeVPN Protocol Configuration\n"
	config += "# Generated automatically - keep this file secure!\n"
	config += "# Do not share your ClientPrivateKey with anyone.\n"
	
	return config
}

// ParseConfig parses a configuration file
func ParseConfig(filepath string) (*Config, error) {
	data, err := os.ReadFile(filepath)
	if err != nil {
		return nil, err
	}
	
	// Simple parser (in production, use proper INI parser)
	config := &Config{}
	lines := string(data)
	
	// Parse lines (simplified)
	// In production, use a proper INI parser like gopkg.in/ini.v1
	fmt.Sscanf(lines, "%s", &config.ServerHost) // Simplified
	
	return config, nil
}

