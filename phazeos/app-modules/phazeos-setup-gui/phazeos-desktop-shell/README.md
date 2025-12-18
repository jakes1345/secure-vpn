# PhazeOS Desktop Shell

## Revolutionary Concept: "The Internet IS Your Desktop"

A web-based desktop environment where there's no distinction between local apps and web content. Everything runs in a browser-based interface with privacy and VPN integration at the core.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  PhazeBrowser (Kiosk Mode)          │
│  ┌───────────────────────────────────────────────┐  │
│  │         http://localhost:8080                 │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │      PhazeOS Desktop Shell (Web UI)     │  │  │
│  │  │                                         │  │  │
│  │  │  • App Launcher                        │  │  │
│  │  │  • File Manager                        │  │  │
│  │  │  • VPN Dashboard                       │  │  │
│  │  │  • Privacy Stats                       │  │  │
│  │  │  • System Settings                     │  │  │
│  │  │  • Workspace Cards                     │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────┐
│           Go Backend (HTTP + WebSocket)             │
│  • System API (launch apps, manage processes)      │
│  • File API (browse, upload, download)             │
│  • VPN API (status, connect, disconnect)           │
│  • Privacy API (tracker stats, firewall)           │
│  • Settings API (themes, preferences)              │
└─────────────────────────────────────────────────────┘
```

## Features

### Core Desktop
- **Unified Interface** - No distinction between apps and web
- **Card-Based UI** - Everything is a draggable card
- **Workspace Management** - Group cards into workspaces
- **Smart Launcher** - Type to search apps, files, and web

### Privacy-First
- **VPN Dashboard** - Always-visible VPN status
- **Tracker Blocking** - Live stats on blocked trackers
- **Firewall Status** - Real-time network monitoring
- **Privacy Score** - Daily privacy rating

### Revolutionary Features
- **Cross-Platform** - Same UI on desktop, mobile, web
- **Remote Access** - SSH tunnel to access from anywhere
- **Offline-First** - Works without internet
- **Infinitely Customizable** - HTML/CSS/JS theming

## Tech Stack

- **Frontend:** Vanilla HTML/CSS/JS (no frameworks)
- **Backend:** Go (HTTP server + WebSocket)
- **Display:** PhazeBrowser in kiosk mode
- **IPC:** WebSockets for real-time updates
- **Storage:** JSON files (simple, portable)

## File Structure

```
phazeos-desktop-shell/
├── server/
│   ├── main.go              # HTTP server entry point
│   ├── api/
│   │   ├── apps.go          # App launcher API
│   │   ├── files.go         # File manager API
│   │   ├── vpn.go           # VPN status/control
│   │   ├── privacy.go       # Privacy stats
│   │   └── system.go        # System info
│   └── ws/
│       └── websocket.go     # WebSocket handler
├── web/
│   ├── index.html           # Main UI
│   ├── css/
│   │   ├── style.css        # Core styles
│   │   └── themes/          # Theme variants
│   ├── js/
│   │   ├── app.js           # Main app logic
│   │   ├── launcher.js      # App launcher
│   │   ├── files.js         # File manager
│   │   ├── vpn.js           # VPN widget
│   │   └── privacy.js       # Privacy dashboard
│   └── assets/
│       ├── icons/           # UI icons
│       └── wallpapers/      # Default wallpapers
└── config/
    └── desktop.json         # Desktop configuration
```

## Installation

1. Build the Go server
2. Copy to `/opt/phazeos-shell`
3. Configure Labwc to launch PhazeBrowser in kiosk mode
4. PhazeBrowser loads `http://localhost:8080`

## Development

```bash
cd server
go build -o phazeos-shell
./phazeos-shell
```

Then open browser to `http://localhost:8080`

## Design Philosophy

1. **Privacy by Default** - VPN/firewall always visible
2. **Simplicity** - No learning curve, it's just a webpage
3. **Transparency** - Open source, auditable
4. **Flexibility** - Users can customize everything
5. **Uniqueness** - No other OS does this

---

**Status:** 🚧 In Development
**Target:** PhazeOS Alpha v1.0
