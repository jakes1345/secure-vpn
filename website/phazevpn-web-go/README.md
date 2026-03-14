# PhazeVPN Architecture Handoff

**Last Updated:** December 17, 2025
**Status:** ✅ Production Ready / Beta

## 🚀 System Overview

The PhazeVPN ecosystem has been completely rebuilt from Python to a high-performance **Go** architecture.

### **1. Web Backend (`/phazevpn-web-go`)**
- **Language:** Go 1.22+
- **Entry Point:** `main.go`
- **Database:** SQLite3 (`phazevpn.db`)
- **Key Features:**
  - **Authentication:** bcrypt password hashing, secure session tokens.
  - **Email:** Integrated SMTP (using local Postfix on VPS) for verification and password resets.
  - **VPN Keys:** Generates WireGuard, OpenVPN, and PhazeVPN configs on demand.
  - **API:** Provides endpoints (`/api/login`, `/api/vpn/keys`) for the GUI client.
  - **UI/UX:** Modern Cyberpunk-themed HTML/CSS with server-side template rendering.

### **2. VPN Protocol & Clients (`/phazevpn-protocol-go`)**
- **Language:** Go
- **Components:**
  - `cmd/phazevpn-client`: Minimal CLI client.
  - `cmd/phazevpn-gui`: **Active GUI Client** with Fyne.
    - Features: Login window, auto-config, connecting/disconnecting, stats.
- **Builds:**
  - Linux: `PhazeVPN-Linux` (Native binary)
  - Windows/Mac: Requires cross-compilation with CGO (use `build-gui-clients.sh` variants).

### **3. Infrastructure**
- **Server:** Configured via environment variables (see `.env.example`)
- **Web Server:** Nginx (Reverse Proxy to Go port 5000)
- **VPN Servers:**
  - WireGuard: Port 51820
  - PhazeVPN: Port 51821
  - OpenVPN: Port 1194
- **Email:** Postfix (SMTP Port 25, local delivery)

## 📂 Repository Structure

```
/
├── phazevpn-web-go/       # [NEW] The entire web platform (Go)
│   ├── main.go            # Web server & API handlers
│   ├── email.go           # Email sending logic
│   ├── templates/         # HTML Templates
│   └── static/            # CSS/JS assets
├── phazevpn-protocol-go/  # [NEW] VPN Client Source code
│   └── cmd/phazevpn-gui/  # The GUI Client source
├── client-builds/         # compiled CLI binaries
├── phazebrowser-gecko/    # PhazeBrowser source
├── SESSION_COMPLETE.md    # Detailed session log
├── HONEST_STATUS.md       # Roadmap & Current Status
└── TESTING_CHECKLIST.md   # QA Tests
```

## 🛠️ How to Deploy

**Website:**
Run `./deploy-website.sh`. This builds the Go binary, packages it with templates, scp's to VPS, and restarts the service.

**Clients:**
Run `./build-all-clients.sh` for CLI clients.
For GUI clients, build natively on the target OS (see `GUI_BUILD_INSTRUCTIONS.md`).

## ⚠️ Known Large Files (Ignored)
- `phazeos-from-scratch/sources/*`: Large binary downloads for OS build.
- `_ARCHIVE_OLD_FILES/*`: Backupzips.
These are excluded from git.
