package api

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"os/exec"
	"strconv"
	"strings"
)

type VPNStatus struct {
	Connected bool   `json:"connected"`
	Server    string `json:"server"`
	IP        string `json:"ip"`
	Bandwidth struct {
		Download string `json:"download"`
		Upload   string `json:"upload"`
	} `json:"bandwidth"`
	Latency string `json:"latency"`
	Uptime  string `json:"uptime"`
}

// GetVPNStatus returns REAL VPN status from WireGuard
func GetVPNStatus(w http.ResponseWriter, r *http.Request) {
	status := VPNStatus{}

	// Check WireGuard interface
	cmd := exec.Command("wg", "show", "wg0")
	output, err := cmd.Output()

	if err != nil || len(output) == 0 {
		// Not connected
		status.Connected = false
		status.Server = "Disconnected"
		status.IP = getRealPublicIP()
		status.Bandwidth.Download = "0 B/s"
		status.Bandwidth.Upload = "0 B/s"
		status.Latency = "N/A"
		status.Uptime = "0s"
	} else {
		// Connected
		status.Connected = true

		// Parse server location from config
		configData, _ := ioutil.ReadFile("/etc/wireguard/wg0.conf")
		if strings.Contains(string(configData), "51.91.121.135") {
			status.Server = "France (OVH)"
		} else {
			status.Server = "PhazeVPN Server"
		}

		// Get real public IP
		status.IP = getRealPublicIP()

		// Get bandwidth from /proc/net/dev
		bandwidth := getRealBandwidth()
		status.Bandwidth.Download = bandwidth.Download
		status.Bandwidth.Upload = bandwidth.Upload

		// Get latency
		status.Latency = getLatency("51.91.121.135")

		// Parse uptime from wg output
		status.Uptime = parseWGUptime(string(output))
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

func getRealPublicIP() string {
	// Try multiple IP services for reliability
	services := []string{
		"https://api.ipify.org",
		"https://icanhazip.com",
		"https://ifconfig.me/ip",
	}

	for _, service := range services {
		resp, err := http.Get(service)
		if err != nil {
			continue
		}
		defer resp.Body.Close()

		ip, err := ioutil.ReadAll(resp.Body)
		if err == nil && len(ip) > 0 {
			return strings.TrimSpace(string(ip))
		}
	}

	return "Unknown"
}

func getRealBandwidth() struct{ Download, Upload string } {
	// Read from /proc/net/dev for wg0 interface
	data, err := ioutil.ReadFile("/proc/net/dev")
	if err != nil {
		return struct{ Download, Upload string }{"0 B/s", "0 B/s"}
	}

	lines := strings.Split(string(data), "\n")

	for _, line := range lines {
		if strings.Contains(line, "wg0:") {
			fields := strings.Fields(line)
			if len(fields) >= 10 {
				rxBytes, _ := strconv.ParseInt(fields[1], 10, 64)
				txBytes, _ := strconv.ParseInt(fields[9], 10, 64)

				return struct{ Download, Upload string }{
					Download: formatBytes(rxBytes) + "/s",
					Upload:   formatBytes(txBytes) + "/s",
				}
			}
		}
	}

	return struct{ Download, Upload string }{"0 B/s", "0 B/s"}
}

func getLatency(server string) string {
	cmd := exec.Command("ping", "-c", "1", "-W", "1", server)
	output, err := cmd.Output()
	if err != nil {
		return "N/A"
	}

	// Parse ping time
	if strings.Contains(string(output), "time=") {
		parts := strings.Split(string(output), "time=")
		if len(parts) > 1 {
			timeStr := strings.Split(parts[1], " ")[0]
			return timeStr + " ms"
		}
	}

	return "N/A"
}

func parseWGUptime(output string) string {
	// Parse "latest handshake" from wg show output
	if strings.Contains(output, "latest handshake:") {
		lines := strings.Split(output, "\n")
		for _, line := range lines {
			if strings.Contains(line, "latest handshake:") {
				parts := strings.Split(line, ":")
				if len(parts) > 1 {
					return strings.TrimSpace(parts[1])
				}
			}
		}
	}

	return "Unknown"
}

func formatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return strconv.FormatInt(bytes, 10) + " B"
	}

	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}

	units := []string{"KB", "MB", "GB", "TB"}
	return strconv.FormatFloat(float64(bytes)/float64(div), 'f', 1, 64) + " " + units[exp]
}

// ToggleVPN connects or disconnects VPN
func ToggleVPN(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Check current status
	cmd := exec.Command("wg", "show", "wg0")
	_, err := cmd.Output()

	var result map[string]string

	if err != nil {
		// Not connected, try to connect
		cmd = exec.Command("wg-quick", "up", "wg0")
		if err := cmd.Run(); err != nil {
			result = map[string]string{
				"status":  "error",
				"message": "Failed to connect VPN",
			}
		} else {
			result = map[string]string{
				"status":  "connected",
				"message": "VPN connected successfully",
			}
		}
	} else {
		// Connected, disconnect
		cmd = exec.Command("wg-quick", "down", "wg0")
		if err := cmd.Run(); err != nil {
			result = map[string]string{
				"status":  "error",
				"message": "Failed to disconnect VPN",
			}
		} else {
			result = map[string]string{
				"status":  "disconnected",
				"message": "VPN disconnected successfully",
			}
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}
