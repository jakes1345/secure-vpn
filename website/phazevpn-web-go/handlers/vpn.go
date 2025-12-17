package handlers

import (
	"encoding/json"
	"net/http"
	"phazevpn-web/database"
	"phazevpn-web/models"
	"strconv"

	"github.com/gorilla/mux"
)

// VPNClients renders the VPN clients page
func VPNClients(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)

	clients, err := models.GetUserClients(database.DB, userID)
	if err != nil {
		http.Error(w, "Failed to load clients", http.StatusInternalServerError)
		return
	}

	data := map[string]interface{}{
		"Clients": clients,
	}

	templates.ExecuteTemplate(w, "vpn-clients.html", data)
}

// CreateVPNClient creates a new VPN client
func CreateVPNClient(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)

	name := r.FormValue("name")
	protocol := r.FormValue("protocol")

	if name == "" || protocol == "" {
		http.Error(w, "Name and protocol are required", http.StatusBadRequest)
		return
	}

	// TODO: Generate keys and config based on protocol
	// For now, just create the client record

	_, err := database.DB.Exec(`
		INSERT INTO clients (user_id, name, protocol, ip_address, created_at)
		VALUES (?, ?, ?, '10.8.0.2', NOW())
	`, userID, name, protocol)

	if err != nil {
		http.Error(w, "Failed to create client", http.StatusInternalServerError)
		return
	}

	http.Redirect(w, r, "/vpn/clients", http.StatusSeeOther)
}

// DeleteVPNClient deletes a VPN client
func DeleteVPNClient(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)
	vars := mux.Vars(r)
	clientID := vars["id"]

	// Verify client belongs to user
	_, err := database.DB.Exec(`
		DELETE FROM clients WHERE id = ? AND user_id = ?
	`, clientID, userID)

	if err != nil {
		http.Error(w, "Failed to delete client", http.StatusInternalServerError)
		return
	}

	http.Redirect(w, r, "/vpn/clients", http.StatusSeeOther)
}

// DownloadConfig generates and downloads VPN config
func DownloadConfig(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)
	vars := mux.Vars(r)
	clientID, _ := strconv.Atoi(vars["id"])

	// Get client
	var client models.Client
	err := database.DB.QueryRow(`
		SELECT id, name, protocol FROM clients WHERE id = ? AND user_id = ?
	`, clientID, userID).Scan(&client.ID, &client.Name, &client.Protocol)

	if err != nil {
		http.Error(w, "Client not found", http.StatusNotFound)
		return
	}

	// Generate config based on protocol
	var config string
	var filename string

	switch client.Protocol {
	case "openvpn":
		config = generateOpenVPNConfig(client)
		filename = client.Name + ".ovpn"
	case "wireguard":
		config = generateWireGuardConfig(client)
		filename = client.Name + ".conf"
	case "phazevpn":
		config = generatePhazeVPNConfig(client)
		filename = client.Name + "-phazevpn.conf"
	default:
		http.Error(w, "Unknown protocol", http.StatusBadRequest)
		return
	}

	// Send file
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Disposition", "attachment; filename="+filename)
	w.Write([]byte(config))
}

// generateOpenVPNConfig generates OpenVPN config
func generateOpenVPNConfig(client models.Client) string {
	return `client
dev tun
proto udp
remote phazevpn.com 1194
resolv-retry infinite
nobind
persist-key
persist-tun
cipher AES-256-GCM
auth SHA256
key-direction 1
verb 3

<ca>
# CA cert here
</ca>

<cert>
# Client cert here
</cert>

<key>
# Client key here
</key>

<tls-auth>
# TLS auth key here
</tls-auth>
`
}

// generateWireGuardConfig generates WireGuard config
func generateWireGuardConfig(client models.Client) string {
	return `[Interface]
PrivateKey = <client-private-key>
Address = 10.7.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = <server-public-key>
Endpoint = phazevpn.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
`
}

// generatePhazeVPNConfig generates PhazeVPN config
func generatePhazeVPNConfig(client models.Client) string {
	return `[server]
address = phazevpn.com
port = 51821

[network]
client_ip = 10.9.0.2/24
dns = 1.1.1.1,1.0.0.1

[security]
encryption = chacha20-poly1305
hash = sha512

[options]
kill_switch = true
obfuscation = true
reconnect = true
`
}

// API Handlers

// APIStatus returns service status
func APIStatus(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "ok",
		"version": "1.0.0",
	})
}

// APIVersion returns API version
func APIVersion(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]interface{}{
		"version": "1.0.0",
		"api":     "v1",
	})
}

// APIUser returns current user info
func APIUser(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)
	username := r.Context().Value("username").(string)
	role := r.Context().Value("role").(string)

	json.NewEncoder(w).Encode(map[string]interface{}{
		"id":       userID,
		"username": username,
		"role":     role,
	})
}

// APIClients returns user's VPN clients
func APIClients(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)

	clients, err := models.GetUserClients(database.DB, userID)
	if err != nil {
		http.Error(w, "Failed to load clients", http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(clients)
}

// APIStats returns user statistics
func APIStats(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)

	clients, _ := models.GetUserClients(database.DB, userID)

	json.NewEncoder(w).Encode(map[string]interface{}{
		"total_clients":  len(clients),
		"active_clients": 0, // TODO: Track active connections
		"bandwidth_used": 0, // TODO: Track bandwidth
	})
}
