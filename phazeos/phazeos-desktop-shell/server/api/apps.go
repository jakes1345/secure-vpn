package api

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

type Application struct {
	Name        string `json:"name"`
	Exec        string `json:"exec"`
	Icon        string `json:"icon"`
	Category    string `json:"category"`
	Description string `json:"description"`
}

// GetApplications returns REAL applications from .desktop files
func GetApplications(w http.ResponseWriter, r *http.Request) {
	apps := []Application{}

	// Scan /usr/share/applications for .desktop files
	desktopDirs := []string{
		"/usr/share/applications",
		"/usr/local/share/applications",
		"/home/admin/.local/share/applications",
	}

	for _, dir := range desktopDirs {
		files, err := filepath.Glob(filepath.Join(dir, "*.desktop"))
		if err != nil {
			continue
		}

		for _, file := range files {
			app := parseDesktopFile(file)
			if app != nil {
				apps = append(apps, *app)
			}
		}
	}

	// Add custom Phaze apps (high priority)
	phazeApps := []Application{
		{
			Name:        "PhazeBrowser",
			Exec:        "/usr/bin/phazebrowser_native",
			Icon:        "🌐",
			Category:    "Internet",
			Description: "Privacy-focused web browser",
		},
		{
			Name:        "PhazeVPN",
			Exec:        "/usr/bin/phazevpn-gui",
			Icon:        "🔒",
			Category:    "Network",
			Description: "VPN client and manager",
		},
		{
			Name:        "Terminal",
			Exec:        "foot",
			Icon:        "💻",
			Category:    "System",
			Description: "Terminal emulator",
		},
		{
			Name:        "Text Editor",
			Exec:        "nano",
			Icon:        "📝",
			Category:    "Accessories",
			Description: "Text editor",
		},
		{
			Name:        "System Monitor",
			Exec:        "htop",
			Icon:        "📊",
			Category:    "System",
			Description: "System resource monitor",
		},
	}

	// Prepend Phaze apps
	apps = append(phazeApps, apps...)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(apps)
}

func parseDesktopFile(path string) *Application {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return nil
	}

	app := &Application{}
	lines := strings.Split(string(data), "\n")
	inDesktopEntry := false

	for _, line := range lines {
		line = strings.TrimSpace(line)

		if line == "[Desktop Entry]" {
			inDesktopEntry = true
			continue
		}

		if strings.HasPrefix(line, "[") && line != "[Desktop Entry]" {
			inDesktopEntry = false
		}

		if !inDesktopEntry {
			continue
		}

		if strings.HasPrefix(line, "Name=") && app.Name == "" {
			app.Name = strings.TrimPrefix(line, "Name=")
		}

		if strings.HasPrefix(line, "Exec=") {
			exec := strings.TrimPrefix(line, "Exec=")
			// Clean up exec string (remove %u, %f, etc.)
			exec = strings.ReplaceAll(exec, "%u", "")
			exec = strings.ReplaceAll(exec, "%U", "")
			exec = strings.ReplaceAll(exec, "%f", "")
			exec = strings.ReplaceAll(exec, "%F", "")
			app.Exec = strings.TrimSpace(exec)
		}

		if strings.HasPrefix(line, "Icon=") {
			icon := strings.TrimPrefix(line, "Icon=")
			// Map common icon names to emojis
			app.Icon = mapIconToEmoji(icon)
		}

		if strings.HasPrefix(line, "Categories=") {
			cats := strings.TrimPrefix(line, "Categories=")
			categories := strings.Split(cats, ";")
			if len(categories) > 0 {
				app.Category = categories[0]
			}
		}

		if strings.HasPrefix(line, "Comment=") {
			app.Description = strings.TrimPrefix(line, "Comment=")
		}

		// Skip hidden or no-display apps
		if strings.HasPrefix(line, "NoDisplay=true") || strings.HasPrefix(line, "Hidden=true") {
			return nil
		}
	}

	// Only return if we have at least name and exec
	if app.Name != "" && app.Exec != "" {
		return app
	}

	return nil
}

func mapIconToEmoji(iconName string) string {
	iconMap := map[string]string{
		"firefox":             "🦊",
		"chromium":            "🌐",
		"chrome":              "🌐",
		"terminal":            "💻",
		"utilities-terminal":  "💻",
		"text-editor":         "📝",
		"gedit":               "📝",
		"nano":                "📝",
		"vim":                 "📝",
		"files":               "📁",
		"nautilus":            "📁",
		"thunar":              "📁",
		"system-file-manager": "📁",
		"settings":            "⚙️",
		"preferences":         "⚙️",
		"multimedia":          "🎵",
		"video":               "🎬",
		"image":               "🖼️",
		"gimp":                "🎨",
		"inkscape":            "🎨",
		"libreoffice":         "📄",
		"writer":              "📄",
		"calc":                "📊",
		"mail":                "📧",
		"thunderbird":         "📧",
		"network":             "🌐",
		"transmission":        "⬇️",
		"steam":               "🎮",
		"discord":             "💬",
		"slack":               "💬",
		"code":                "💻",
		"vscode":              "💻",
	}

	iconLower := strings.ToLower(iconName)

	for key, emoji := range iconMap {
		if strings.Contains(iconLower, key) {
			return emoji
		}
	}

	// Default icons by category
	if strings.Contains(iconLower, "game") {
		return "🎮"
	}
	if strings.Contains(iconLower, "media") || strings.Contains(iconLower, "audio") {
		return "🎵"
	}
	if strings.Contains(iconLower, "video") {
		return "🎬"
	}
	if strings.Contains(iconLower, "graphics") {
		return "🎨"
	}
	if strings.Contains(iconLower, "office") || strings.Contains(iconLower, "document") {
		return "📄"
	}

	return "📦" // Default
}

// LaunchApp launches an application
func LaunchApp(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		App string `json:"app"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Set environment for Wayland
	os.Setenv("WAYLAND_DISPLAY", "wayland-0")
	os.Setenv("XDG_RUNTIME_DIR", "/run/user/1000")

	// Launch app in background
	cmd := exec.Command("sh", "-c", req.App+" &")
	if err := cmd.Start(); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status": "launched",
		"app":    req.App,
	})
}
