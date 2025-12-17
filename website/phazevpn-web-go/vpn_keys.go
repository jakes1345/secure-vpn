package main

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
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
	return fmt.Sprintf(`[Interface]
PrivateKey = %s
Address = %s/24
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = C0PyFZkqPkyeHPVrnpjYnoG6J+ddhAtr8Et85cwZoXM=
Endpoint = phazevpn.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
`, privateKey, clientIP)
}

// CreateOpenVPNConfig creates an OpenVPN client config
func CreateOpenVPNConfig(username string) string {
	return fmt.Sprintf(`client
dev tun
proto udp
remote phazevpn.com 1194
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
`, username)
}

// CreatePhazeVPNConfig creates a PhazeVPN client config
func CreatePhazeVPNConfig(username, phazeKey string) string {
	return fmt.Sprintf(`# PhazeVPN Configuration
# User: %s

[connection]
server = phazevpn.com
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
dns = 1.1.1.1,1.0.0.1

[performance]
mtu = 1420
keepalive = 25
`, username, username, phazeKey)
}
