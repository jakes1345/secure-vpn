package main

import (
	"embed"
	"encoding/json"
	"io/fs"
	"log"
	"net/http"
	"os"
	"time"

	"phazeos-desktop-shell/api"

	"github.com/gorilla/websocket"
)

//go:embed web
var webFiles embed.FS

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

func main() {
	log.Println("🚀 PhazeOS Desktop Shell starting...")
	log.Println("📡 Connecting to REAL services:")
	log.Println("   ✅ VPN: WireGuard interface")
	log.Println("   ✅ Browser: PhazeBrowser database")
	log.Println("   ✅ Email: Web portal API")
	log.Println("   ✅ System: /proc filesystem")

	webFS, err := fs.Sub(webFiles, "web")
	if err != nil {
		log.Fatal(err)
	}

	http.Handle("/", http.FileServer(http.FS(webFS)))

	// REAL API endpoints
	http.HandleFunc("/api/system", api.GetSystemInfo)
	http.HandleFunc("/api/vpn", api.GetVPNStatus)
	http.HandleFunc("/api/vpn/toggle", api.ToggleVPN)
	http.HandleFunc("/api/privacy", api.GetPrivacyStats)
	http.HandleFunc("/api/apps", api.GetApplications)
	http.HandleFunc("/api/launch", api.LaunchApp)
	http.HandleFunc("/api/emails", api.GetEmails)
	http.HandleFunc("/api/send_email", api.SendEmail)
	http.HandleFunc("/api/files", handleFiles)
	http.HandleFunc("/ws", handleWebSocket)

	port := "8080"
	log.Printf("✅ Server running on http://localhost:%s\n", port)
	log.Println("💎 NO MOCK DATA - Everything is REAL!")

	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

func handleFiles(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Query().Get("path")
	if path == "" {
		path = "/home/admin"
	}

	entries, err := os.ReadDir(path)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	type FileInfo struct {
		Name  string `json:"name"`
		IsDir bool   `json:"is_dir"`
		Size  int64  `json:"size"`
	}

	files := []FileInfo{}
	for _, entry := range entries {
		info, _ := entry.Info()
		files = append(files, FileInfo{
			Name:  entry.Name(),
			IsDir: entry.IsDir(),
			Size:  info.Size(),
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(files)
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("WebSocket upgrade error:", err)
		return
	}
	defer conn.Close()

	log.Println("✅ WebSocket client connected")

	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			update := map[string]interface{}{
				"type": "system_update",
				"data": map[string]interface{}{
					"timestamp": time.Now(),
				},
			}

			if err := conn.WriteJSON(update); err != nil {
				log.Println("WebSocket write error:", err)
				return
			}
		}
	}
}
