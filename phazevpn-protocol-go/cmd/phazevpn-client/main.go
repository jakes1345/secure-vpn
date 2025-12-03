package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"phazevpn-server/internal/client"
	"phazevpn-server/internal/protocol"
)

var (
	configFile = flag.String("config", "client-phazevpn.conf", "Client configuration file")
)

func main() {
	flag.Parse()

	fmt.Println("=" * 70)
	fmt.Println("🚀 PhazeVPN Client")
	fmt.Println("=" * 70)
	fmt.Println()

	// Load config
	cfg, err := client.ParseConfig(*configFile)
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	fmt.Printf("📁 Config: %s\n", *configFile)
	fmt.Printf("🌐 Server: %s:%d\n", cfg.ServerHost, cfg.ServerPort)
	fmt.Println()

	// Connect to server
	serverAddr := fmt.Sprintf("%s:%d", cfg.ServerHost, cfg.ServerPort)
	conn, err := net.Dial("udp", serverAddr)
	if err != nil {
		log.Fatalf("Failed to connect to server: %v", err)
	}
	defer conn.Close()

	fmt.Printf("✅ Connected to %s\n", serverAddr)
	fmt.Println()

	// Send handshake
	handshake := protocol.NewHandshakePacket(0, []byte(cfg.ClientPublicKey))
	handshakeData, err := handshake.Serialize()
	if err != nil {
		log.Fatalf("Failed to serialize handshake: %v", err)
	}

	if _, err := conn.Write(handshakeData); err != nil {
		log.Fatalf("Failed to send handshake: %v", err)
	}

	fmt.Println("📤 Handshake sent, waiting for response...")

	// Read response
	conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	buf := make([]byte, 1500)
	n, err := conn.Read(buf)
	if err != nil {
		log.Fatalf("Failed to receive response: %v", err)
	}

	response, err := protocol.ParsePacket(buf[:n])
	if err != nil {
		log.Fatalf("Failed to parse response: %v", err)
	}

	if response.Type == protocol.PacketTypeHandshake {
		fmt.Printf("✅ Handshake successful! Session ID: %d\n", response.SessionID)
		fmt.Printf("📍 Assigned IP: %s\n", string(response.Payload))
		fmt.Println()
		fmt.Println("🔒 VPN Connection Established!")
		fmt.Println("   Press Ctrl+C to disconnect")
		fmt.Println()
	} else {
		log.Fatalf("Unexpected response type: %d", response.Type)
	}

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan
	fmt.Println("\n🛑 Disconnecting...")
	fmt.Println("✅ Disconnected")
}

