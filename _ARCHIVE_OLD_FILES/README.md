# PhazeVPN - Secure VPN Browser

A custom web browser with integrated VPN connection built with GTK/WebKit2, featuring comprehensive privacy protection, ad blocking, and tracking prevention.

## Features

### 🔒 VPN Integration
- **Multi-Protocol Support**: OpenVPN, WireGuard, and PhazeVPN protocols
- **Auto-Download Configs**: Automatically fetches VPN configurations from web portal
- **Connection Management**: Connect/disconnect VPN directly from browser
- **VPN Statistics**: Real-time connection stats, latency, and data usage
- **Kill Switch**: Blocks browsing when VPN disconnects
- **Auto-Reconnect**: Automatically reconnects on connection loss

### 🛡️ Privacy & Security
- **Comprehensive Ad Blocking**: Blocks ads using EasyList and EasyPrivacy filter lists
- **Tracking Protection**: Blocks tracking scripts, cookies, and fingerprinting
- **Fingerprint Protection**: Makes all users appear identical (anti-fingerprinting)
- **DNS over HTTPS (DoH)**: Encrypted DNS resolution
- **Maximum Privacy Mode**: Comprehensive protection against tracking and identification

### 🎨 Modern UI/UX
- **Modern Purple Theme**: Beautiful gradient interface with purple accents
- **Multiple Themes**: Default, Light, and Dark themes
- **Tab Management**: Modern tab interface with favicon support
- **VPN Status Bar**: Prominent status bar showing VPN connection state
- **Responsive Design**: Clean, modern interface

### 🌐 Browser Features
- **Web Portal Login**: Login to web portal and fetch VPN clients automatically
- **Download Manager**: Track and manage file downloads
- **Bookmarks**: Save and manage bookmarks
- **History**: Browsing history tracking
- **Password Manager**: Secure password storage (planned)

## Installation

### Requirements
```bash
sudo apt-get update
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 python3-requests
```

### Running the Browser
```bash
python3 phazebrowser.py
```

## Configuration

The browser automatically:
- Downloads VPN configs from the web portal
- Loads ad blocking filter lists (EasyList, EasyPrivacy)
- Creates configuration directory at `~/.config/phazebrowser/`

## VPN Setup

1. **Connect to VPN**: Click "Connect VPN" in the status bar
2. **Login to Portal**: Use "Login" button to authenticate with web portal
3. **Auto-Download**: Configs are automatically downloaded if missing
4. **Select Server**: Choose from available VPN servers

## Privacy Features

### Ad Blocking
- Blocks ads using comprehensive filter lists
- Network-level request filtering
- CSS and JavaScript-based blocking

### Tracking Protection
- Blocks tracking scripts and cookies
- Prevents fingerprinting through:
  - Canvas fingerprinting protection
  - WebGL fingerprinting protection
  - Audio fingerprinting protection
  - Font fingerprinting protection
  - Screen resolution spoofing
  - Timezone normalization
  - Navigator API spoofing
  - WebRTC leak prevention
  - Battery API blocking
  - Geolocation blocking
  - Media devices enumeration blocking
  - Connection API spoofing
  - Performance API normalization

## Development

### Project Structure
```
secure-vpn/
├── phazebrowser.py          # Main browser application
├── deploy-phazebrowser-vps.py  # Deployment script
├── download-browser-from-vps.sh # Download script
├── web-portal/              # Web portal application
└── README.md               # This file
```

### Deployment
The browser can be deployed to a VPS using:
```bash
python3 deploy-phazebrowser-vps.py
```

## License

Proprietary - PhazeVPN

## Support

For issues or questions, contact the PhazeVPN team.
