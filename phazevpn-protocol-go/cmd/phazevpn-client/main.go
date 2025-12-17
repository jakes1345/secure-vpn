package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"phazevpn-server/internal/client"
)

var (
	serverAddr = flag.String("server", "15.204.11.19", "Server address")
	serverPort = flag.Int("port", 51821, "Server port")
	vpnNetwork = flag.String("network", "10.9.0.0/24", "VPN network")
	clientIP   = flag.String("ip", "10.9.0.2", "Client IP address")
	configFile = flag.String("config", "", "Config file path")
)

func main() {
	flag.Parse()

	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("🚀 PhazeVPN Client - Secure VPN Connection")
	fmt.Println(strings.Repeat("=", 70))
	fmt.Printf("📍 Server: %s:%d\n", *serverAddr, *serverPort)
	fmt.Printf("🌐 VPN Network: %s\n", *vpnNetwork)
	fmt.Printf("💻 Client IP: %s\n", *clientIP)
	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("")

	// Check root privileges
	if os.Geteuid() != 0 {
		log.Fatal("❌ This program must be run as root (for TUN interface creation)")
	}

	// Create client
	vpnClient, err := client.NewPhazeVPNClient(*serverAddr, *serverPort, *vpnNetwork, *clientIP)
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}

	// Connect
	if err := vpnClient.Connect(); err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}

	// Print stats periodically
	go printStats(vpnClient)

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan
	fmt.Println("\n🛑 Shutting down...")
	vpnClient.Disconnect()
	fmt.Println("✅ Client stopped")
}

func printStats(c *client.PhazeVPNClient) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		if !c.IsConnected() {
			continue
		}

		sent, recv := c.GetStats()
		fmt.Printf("📊 Stats: ⬆️  %s sent | ⬇️  %s received\n",
			formatBytes(sent), formatBytes(recv))
	}
}

func formatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}

	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}

	units := []string{"KB", "MB", "GB", "TB"}
	return fmt.Sprintf("%.1f %s", float64(bytes)/float64(div), units[exp])
}
