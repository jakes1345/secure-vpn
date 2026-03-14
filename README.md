# PhazeVPN Ecosystem

A complete privacy-focused VPN solution with custom OS, browser, and infrastructure.

## 🏗️ Project Structure

### Core Components

#### 1. **PhazeVPN** (`phazevpn/`)
- Custom VPN protocol implementation in Go
- Server and client components
- Security features: DNS leak protection, IPv6 leak protection, WebRTC blocking
- Kill switch implementation

Mobile apps in PhazeVPN project:
- Android app (`clients/mobile/android-app/`)
- iOS app (`clients/mobile/ios-app/`)

#### 2. **PhazeOS** (`phazeos/phazeos-from-scratch/`)
- Custom Linux distribution built from scratch
- Kernel: Linux 6.7.4 with complete driver support
- Desktop: LabWC (Wayland compositor)
- Privacy-first design
- Live ISO bootable system

#### 3. **PhazeBrowser** (`phazebrowser/`)
- Privacy-focused Firefox-based browser (Gecko is core engine)
- Custom configurations and extensions
- Integrated with PhazeVPN

#### 4. **Web Portal** (`website/go-web-portal/`)
- Go (Gin framework) web application
- User management and authentication
- VPN configuration generation
- Admin dashboard

#### 5. **Go Web Server** (`website/phazevpn-web-go/`)
- Modern Go-based web platform
- bcrypt authentication, session tokens
- API endpoints for VPN management
- HTML template rendering

### Infrastructure

- **Server:** Configured via environment variables (see `.env.example`)
- **Services:** VPN server, web portal, email
- **Deployment:** Environment variable–driven for portability

## 🎯 Key Features

### Security & Privacy
- Custom VPN protocol
- DNS leak protection
- IPv6 leak protection
- WebRTC blocking
- Kill switch
- No-logs policy

### PhazeOS
- Built from scratch for maximum privacy
- Wayland-based desktop
- Pre-configured with PhazeVPN
- Live boot capability
- OverlayFS for persistence

### Web Services
- User registration and authentication
- VPN key management
- Multi-device support
- Admin panel

## 📂 Repository Structure

```
secure-vpn/
├── phazevpn/                   # VPN protocol & clients
│   ├── clients/mobile/         # Android & iOS apps
│   └── vpn-client-configs/     # Config templates
├── phazeos/                    # Custom OS
│   ├── app-modules/            # Desktop shell modules
│   ├── build/                  # Build artifacts
│   └── phazeos-from-scratch/   # Linux from scratch build
├── phazebrowser/               # Privacy browser
├── website/
│   ├── go-web-portal/          # Go/Gin web portal (canonical)
│   ├── phazevpn-web-go/        # Main Go web server
│   └── phasesearch/            # Search page
├── .env.example                # Environment variable reference
├── .gitignore
└── README.md
```

## 🚀 Current Status

### Completed
- ✅ VPN protocol implementation
- ✅ Security features (leak protection)
- ✅ Custom kernel with full driver support
- ✅ PhazeOS Live ISO
- ✅ Go web portal
- ✅ Go web server
- ✅ PhazeBrowser customization

### In Progress
- 🔨 Mobile app development
- 🔨 Additional PhazeOS packages
- 🔨 Documentation

## 🔧 Local Development

### Prerequisites
- Go 1.21+
- WireGuard tools (`wg`)
- SQLite3

### Setup

```bash
# Clone and configure
git clone https://github.com/jakes1345/secure-vpn
cd secure-vpn

# Set up environment variables
cp .env.example .env
# Edit .env with your local values

# Run the web server
cd website/phazevpn-web-go
go run .
# Server starts on localhost:5000

# Or run the Go web portal
cd website/go-web-portal
go run .
```

### PhazeOS ISO
```bash
cd phazeos/phazeos-from-scratch
sudo ./35-build-live-iso.sh
```

### VPN Server
```bash
cd phazevpn
go build -o phazevpn-server cmd/server/main.go
```

## 🌍 Deployment

When deploying to a new server, update your `.env` file:

```env
APP_HOST=your-server.com
APP_PORT=5000
APP_SECRET=$(openssl rand -hex 32)
GIN_MODE=release

VPN_SERVER_HOST=your-server.com
VPN_SERVER_ENDPOINT=your-server.com:51820
WG_SERVER_PUBLIC_KEY=<your-wireguard-public-key>

SMTP_HOST=mail.your-server.com
SMTP_PASSWORD=<your-smtp-password>
```

See `.env.example` for the full list of configurable variables.

## 🔐 Security Considerations

- All secrets and server addresses are configured via environment variables
- Never commit `.env` to version control (it is gitignored)
- Rotate credentials immediately if they are ever exposed
- The `APP_SECRET` environment variable must be set to a strong random value in production
- Use `openssl rand -hex 32` to generate a secure secret

## 📧 Contact

- Domain: phazevpn.com
- Email: admin@phazevpn.com

## 📄 License

Copyright © 2026 PhazeVPN. All rights reserved.

