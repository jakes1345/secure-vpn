# 🔒 SecureVPN - Professional VPN Solution

A complete, production-ready VPN server with maximum security encryption and full management capabilities.

## ✨ Features

- **Maximum Security Encryption**
  - ChaCha20-Poly1305 (beyond AES-256)
  - 4096-bit RSA certificates
  - TLS 1.3 minimum
  - Perfect Forward Secrecy

- **Full Management Dashboard**
  - Desktop GUI application
  - Real-time monitoring
  - Client management
  - Statistics and analytics

- **Easy Client Access**
  - Web-based download server
  - One-click config downloads
  - QR code support (coming soon)

- **Production Ready**
  - Systemd integration
  - Auto-start on boot
  - Proper logging
  - Backup/restore

## 🚀 Quick Start

### Installation

**Debian/Ubuntu (.deb package):**
```bash
sudo apt install ./secure-vpn_*.deb
```

**Manual Installation:**
```bash
sudo ./install.sh
```

### Initial Setup

1. **Generate Certificates:**
   ```bash
   cd /opt/secure-vpn
   sudo ./generate-certs.sh
   ```

2. **Configure Firewall:**
   ```bash
   sudo ./setup-routing.sh
   sudo ufw allow 1194/udp
   sudo ufw allow 8081/tcp  # For download server
   ```

3. **Start VPN Server:**
   ```bash
   sudo systemctl start secure-vpn
   sudo systemctl enable secure-vpn
   ```

4. **Launch Dashboard:**
   ```bash
   secure-vpn-gui
   ```

5. **Change Default Password:**
   Edit `/opt/secure-vpn/vpn-gui.py` and change `DEFAULT_PASSWORD`

## 📖 Documentation

- [Installation Guide](README-INSTALL.md)
- [Package Building](README-PACKAGE.md)
- [Security Upgrade Guide](SECURITY-UPGRADE.md)
- [Customization Guide](CUSTOMIZE.md)

## 🎯 Usage

### Command Line

```bash
# VPN Management
sudo secure-vpn start|stop|restart|status
sudo secure-vpn add-client <name>
sudo secure-vpn list-clients

# GUI Dashboard
secure-vpn-gui

# Download Server
sudo secure-vpn-download
# Or: sudo systemctl start secure-vpn-download
```

### GUI Dashboard

Launch from applications menu or run `secure-vpn-gui`

**Features:**
- Start/Stop/Restart VPN server
- View active connections
- Manage clients (add, edit, disconnect, revoke)
- Edit server configuration
- View statistics and logs
- Export client configs
- Backup/restore

## 🔧 Configuration

### Server Config
Edit `/opt/secure-vpn/config/server.conf`

### Client Configs
Located in `/opt/secure-vpn/client-configs/`

### Logs
- Server log: `/opt/secure-vpn/logs/server.log`
- Status log: `/opt/secure-vpn/logs/status.log`

## 🔐 Security

### Default Credentials
⚠️ **CHANGE THE DEFAULT PASSWORD!**

Edit `/opt/secure-vpn/vpn-gui.py`:
```python
DEFAULT_PASSWORD = 'admin123'  # Change this!
```

### Encryption
- Data: ChaCha20-Poly1305 (with AES-256-GCM fallback)
- Certificates: 4096-bit RSA
- TLS: 1.3 minimum
- Hash: SHA512

### Best Practices
1. Change default password immediately
2. Use strong client names
3. Regularly rotate certificates
4. Monitor connection logs
5. Keep system updated
6. Use firewall rules
7. Regular backups

## 📊 Monitoring

### Check Status
```bash
sudo systemctl status secure-vpn
sudo secure-vpn status
```

### View Logs
```bash
tail -f /opt/secure-vpn/logs/server.log
```

### Statistics
Open GUI Dashboard → Statistics tab

## 🛠️ Troubleshooting

### VPN Won't Start
```bash
# Check logs
tail -f /opt/secure-vpn/logs/server.log

# Verify certificates
ls -la /opt/secure-vpn/certs/

# Check config
cat /opt/secure-vpn/config/server.conf
```

### Clients Can't Connect
```bash
# Check firewall
sudo ufw status

# Verify routing
sudo ./setup-routing.sh

# Check server status
sudo systemctl status secure-vpn
```

### No Internet for Clients
```bash
# Setup NAT routing
sudo ./setup-routing.sh

# Verify IP forwarding
cat /proc/sys/net/ipv4/ip_forward  # Should be 1
```

## 📦 Package Management

### Install
```bash
sudo apt install ./secure-vpn_*.deb
```

### Update
```bash
sudo apt install --reinstall ./secure-vpn_*.deb
```

### Remove
```bash
sudo apt remove secure-vpn
```

## 🔄 Updates

Check for updates and rebuild package:
```bash
git pull  # If using git
./build-deb.sh
sudo apt install --reinstall ./secure-vpn_*.deb
```

## 📝 License

MIT License - See LICENSE file

## 🤝 Support

- Check logs: `/opt/secure-vpn/logs/`
- GUI Dashboard: Statistics and Logs tabs
- Documentation: See README files

## 🎉 Features Roadmap

- [ ] QR code generation for mobile setup
- [ ] Bandwidth limiting per client
- [ ] Connection time limits
- [ ] IP whitelist/blacklist
- [ ] Email notifications
- [ ] Multi-server management
- [ ] Web-based dashboard (alternative to GUI)

---

**Made with 🔒 for maximum security**
