package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"phazevpn-server/internal/client"
)

func main() {
	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("🚀 PhazeVPN Client - Quick Test")
	fmt.Println(strings.Repeat("=", 70))
	fmt.Println()

	// Use environment variable or default to localhost
	serverHost := os.Getenv("VPN_SERVER_HOST")
	if serverHost == "" {
		serverHost = "localhost"
	}
	serverPort := 51820
	clientIP := "10.9.0.100"

	fmt.Printf("🌐 Server: %s:%d\n", serverHost, serverPort)
	fmt.Printf("📍 Client IP: %s\n", clientIP)
	fmt.Println()

	// Create client
	c, err := client.NewPhazeVPNClient(serverHost, 51821, "10.9.0.0/24", "10.9.0.2")
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}

	// Start client
	if err := c.Connect(); err != nil {
		log.Fatalf("Failed to start client: %v", err)
	}

	fmt.Println("✅ Connected! Press Ctrl+C to disconnect")

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan
	fmt.Println("\n🛑 Disconnecting...")
	c.Disconnect()
	fmt.Println("✅ Disconnected")
}
