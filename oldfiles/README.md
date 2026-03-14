# PhazeVPN Ecosystem

A complete privacy-focused VPN solution with custom OS, browser, and infrastructure.

## 🏗️ Project Structure

### Core Components

#### 1. **PhazeVPN Protocol** (`phazevpn-protocol-go/`)
- Custom VPN protocol implementation in Go
- Server and client components
- Security features: DNS leak protection, IPv6 leak protection, WebRTC blocking
- Kill switch implementation

#### 2. **PhazeOS** (`phazeos-from-scratch/`)
- Custom Linux distribution built from scratch
- Kernel: Linux 6.7.4 with complete driver support
- Desktop: LabWC (Wayland compositor)
- Privacy-first design
- Live ISO bootable system

#### 3. **PhazeBrowser** (`phazebrowser-gecko/`)
- Privacy-focused Firefox-based browser
- Custom configurations and extensions
- Integrated with PhazeVPN

#### 4. **Web Portal** (`web-portal/`)
- Python Flask application
- User management and authentication
- VPN configuration generation
- Admin dashboard

#### 5. **Go Web Server** (`phazevpn-web-go/`)
- Modern replacement for Python portal
- JWT authentication
- API endpoints for VPN management

#### 6. **Mobile Apps**
- Android app (`android-app/`)
- iOS app (`ios-app/`)

### Infrastructure

- **VPS**: phazevpn.com
- **Services**: VPN server, web portal, email
- **Deployment scripts**: Automated deployment to VPS

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

## 📂 Important Directories

```
secure-vpn/
├── phazevpn-protocol-go/    # VPN protocol (Go)
├── phazeos-from-scratch/     # Custom OS build
├── phazebrowser-gecko/       # Privacy browser
├── web-portal/               # Python web app
├── phazevpn-web-go/         # Go web server
├── android-app/              # Android client
├── ios-app/                  # iOS client
└── phazeos-scripts/          # System scripts
```

## 🚀 Current Status

### Completed
- ✅ VPN protocol implementation
- ✅ Security features (leak protection)
- ✅ Custom kernel with full driver support
- ✅ PhazeOS Live ISO (683MB)
- ✅ Web portal (Python)
- ✅ Go web server
- ✅ PhazeBrowser customization

### In Progress
- 🔨 Mobile app development
- 🔨 Additional PhazeOS packages
- 🔨 Documentation

## 🔧 Build Instructions

### PhazeOS ISO
```bash
cd phazeos-from-scratch
sudo ./35-build-live-iso.sh
```

### VPN Server
```bash
cd phazevpn-protocol-go
go build -o phazevpn-server cmd/server/main.go
```

### Web Portal
```bash
cd web-portal
pip install -r requirements.txt
python app.py
```

## 📝 Notes for AI Analysis

- **Split codebase**: Some components on NTFS (`/media/jack/Liunux/secure-vpn/`), build artifacts on ext4
- **VPS deployment**: Production services running on phazevpn.com
- **Build challenges**: NTFS filesystem caused segfaults during compilation, resolved by moving to ext4
- **Recent work**: Kernel rebuild with ISO9660 support, ISO creation successful

## 🔐 Security Considerations

- API keys and tokens are gitignored
- VPS credentials stored separately
- No hardcoded secrets in code
- All sensitive data in environment variables

## 📧 Contact

- Domain: phazevpn.com
- Email: admin@phazevpn.com
