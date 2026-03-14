package main

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// VPN key generation functions

// GenerateWireGuardKeys generates a WireGuard keypair
func GenerateWireGuardKeys() (privateKey, publicKey string, err error) {
	// Generate private key
	privCmd := exec.Command("wg", "genkey")
	privOut, err := privCmd.Output()
	if err != nil {
		return "", "", err
	}
	privateKey = strings.TrimSpace(string(privOut))

	// Generate public key from private
	pubCmd := exec.Command("wg", "pubkey")
	pubCmd.Stdin = strings.NewReader(privateKey)
	pubOut, err := pubCmd.Output()
	if err != nil {
		return "", "", err
	}
	publicKey = strings.TrimSpace(string(pubOut))

	return privateKey, publicKey, nil
}

// GeneratePhazeVPNKey generates a PhazeVPN key (32 bytes base64)
func GeneratePhazeVPNKey() (string, error) {
	key := make([]byte, 32)
	_, err := rand.Read(key)
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(key), nil
}

// CreateWireGuardConfig creates a WireGuard client config
func CreateWireGuardConfig(privateKey, serverPublicKey, clientIP string) string {
	dnsServers := os.Getenv("VPN_DNS_SERVERS")
	if dnsServers == "" {
		dnsServers = "1.1.1.1, 1.0.0.1"
	}
	serverEndpoint := os.Getenv("VPN_SERVER_ENDPOINT")
	if serverEndpoint == "" {
		serverEndpoint = "localhost:51820"
	}
	return fmt.Sprintf(`[Interface]
PrivateKey = %s
Address = %s/24
DNS = %s

[Peer]
PublicKey = %s
Endpoint = %s
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
`, privateKey, clientIP, dnsServers, serverPublicKey, serverEndpoint)
}

// CreateOpenVPNConfig creates an OpenVPN client config
func CreateOpenVPNConfig(username string) string {
	serverEndpoint := os.Getenv("VPN_SERVER_HOST")
	if serverEndpoint == "" {
		serverEndpoint = "localhost"
	}
	openvpnEndpoint := os.Getenv("VPN_OPENVPN_ENDPOINT")
	if openvpnEndpoint == "" {
		openvpnEndpoint = serverEndpoint + " 1194"
	}
	return fmt.Sprintf(`client
dev tun
proto udp
remote %s
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA256
key-direction 1
verb 3
auth-user-pass

# Certificate and keys will be embedded here
<ca>
# CA certificate
</ca>

<cert>
# Client certificate for %s
</cert>

<key>
# Client private key
</key>

<tls-auth>
# TLS auth key
</tls-auth>
`, openvpnEndpoint, username)
}

// CreatePhazeVPNConfig creates a PhazeVPN client config
func CreatePhazeVPNConfig(username, phazeKey string) string {
	serverHost := os.Getenv("VPN_SERVER_HOST")
	if serverHost == "" {
		serverHost = "localhost"
	}
	dnsServers := os.Getenv("VPN_DNS_SERVERS")
	if dnsServers == "" {
		dnsServers = "1.1.1.1,1.0.0.1"
	}
	return fmt.Sprintf(`# PhazeVPN Configuration
# User: %s

[connection]
server = %s
port = 51821
protocol = phaze

[authentication]
username = %s
key = %s

[encryption]
cipher = chacha20-poly1305
forward_secrecy = true

[privacy]
leak_protection = true
kill_switch = true
dns = %s

[performance]
mtu = 1420
keepalive = 25
`, username, serverHost, username, phazeKey, dnsServers)
}
