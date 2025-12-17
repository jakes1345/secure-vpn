package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"phazevpn-server/internal/client"
)

var (
	serverHost   = flag.String("server", "", "Server hostname or IP")
	serverPort   = flag.Int("port", 51821, "Server port")
	serverKey    = flag.String("server-key", "", "Server public key")
	vpnNetwork   = flag.String("network", "10.9.0.0/24", "VPN network")
	clientIP     = flag.String("client-ip", "", "Client IP address (auto-assigned if empty)")
	outputFile   = flag.String("output", "", "Output file path (default: client-phazevpn.conf)")
)

func main() {
	flag.Parse()

	if *serverHost == "" {
		fmt.Println("❌ Error: --server is required")
		fmt.Println("\nUsage:")
		fmt.Println("  generate-client --server=15.204.11.19 --server-key=<key> [options]")
		fmt.Println("\nOptions:")
		flag.PrintDefaults()
		os.Exit(1)
	}

	if *serverKey == "" {
		fmt.Println("❌ Error: --server-key is required")
		fmt.Println("Get the server key from: cat /etc/phazevpn/wireguard/server_public.key")
		os.Exit(1)
	}

	// Auto-assign client IP if not provided
	if *clientIP == "" {
		*clientIP = "10.9.0.2" // Would be assigned by server in production
	}

	// Generate config
	cfg, err := client.GenerateConfig(
		*serverHost,
		*serverPort,
		*serverKey,
		*vpnNetwork,
		*clientIP,
	)
	if err != nil {
		fmt.Printf("❌ Failed to generate config: %v\n", err)
		os.Exit(1)
	}

	// Determine output file
	output := *outputFile
	if output == "" {
		output = "client-phazevpn.conf"
	}

	// Save config
	if err := cfg.Save(output); err != nil {
		fmt.Printf("❌ Failed to save config: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("✅ Client Configuration Generated!")
	fmt.Println(strings.Repeat("=", 70))
	fmt.Printf("📁 File: %s\n", output)
	fmt.Printf("🌐 Server: %s:%d\n", *serverHost, *serverPort)
	fmt.Printf("🔑 Client Public Key: %s\n", cfg.ClientPublicKey)
	fmt.Printf("📍 Client IP: %s\n", cfg.ClientIP)
	fmt.Println()
	fmt.Println("📝 Next Steps:")
	fmt.Println("  1. Keep this file secure (contains private key)")
	fmt.Println("  2. Use with PhazeVPN client application")
	fmt.Println("  3. Connect to server using this config")
	fmt.Println()
}

