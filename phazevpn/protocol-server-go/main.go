package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"phazevpn-server/internal/server"
)

var (
	host       = flag.String("host", "0.0.0.0", "Server host")
	port       = flag.Int("port", 51820, "Server port")
	vpnNetwork = flag.String("network", "10.9.0.0/24", "VPN network")
)

func main() {
	flag.Parse()

	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("🚀 PhazeVPN Protocol Server - Go Implementation")
	fmt.Println(strings.Repeat("=", 70))
	fmt.Printf("📍 Listening on %s:%d\n", *host, *port)
	fmt.Printf("🌐 VPN Network: %s\n", *vpnNetwork)
	fmt.Println(strings.Repeat("=", 70))
	fmt.Println("")

	// Create server
	srv, err := server.NewPhazeVPNServer(*host, *port, *vpnNetwork)
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}

	// Start server
	if err := srv.Start(); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan
	fmt.Println("\n🛑 Shutting down...")
	srv.Stop()
	fmt.Println("✅ Server stopped")
}

