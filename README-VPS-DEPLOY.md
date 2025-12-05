# PhazeVPN VPS Deployment Guide

This guide explains how to deploy PhazeVPN services to a VPS using the CMake build system.

## Quick Deploy (On VPS)

If you've already uploaded the source code to your VPS:

```bash
# On the VPS
cd /path/to/secure-vpn
sudo bash deploy-to-vps-cmake.sh
```

This will:
1. Install all dependencies (CMake, Go, Python packages)
2. Build all services using CMake
3. Install to `/opt/phaze-vpn`
4. Configure systemd services
5. Setup firewall and networking

## Build Locally, Deploy to VPS

### Option 1: Build on VPS (Recommended)

1. **Upload source code to VPS:**
   ```bash
   rsync -avz --exclude 'build*' --exclude '__pycache__' \
     ./ user@vps-ip:/root/phaze-vpn/
   ```

2. **SSH to VPS and deploy:**
   ```bash
   ssh user@vps-ip
   cd /root/phaze-vpn
   sudo bash deploy-to-vps-cmake.sh
   ```

### Option 2: Build Locally, Package, Deploy

1. **Build and package locally:**
   ```bash
   ./build-and-deploy-vps.sh
   ```

2. **Upload to VPS:**
   ```bash
   scp phazevpn-vps-deploy.tar.gz deploy-on-vps.sh user@vps-ip:/root/
   ```

3. **Install on VPS:**
   ```bash
   ssh user@vps-ip
   cd /root
   sudo bash deploy-on-vps.sh
   ```

## VPS Requirements

### System Requirements
- Ubuntu 20.04+ or Debian 11+
- Root access
- At least 2GB RAM
- At least 10GB disk space

### Ports Needed
- **22** - SSH
- **80** - HTTP (for web portal)
- **443** - HTTPS (for web portal)
- **1194/udp** - OpenVPN
- **51820/udp** - PhazeVPN Protocol
- **5000/tcp** - Web Portal (internal, behind Nginx)

## Services Deployed

The CMake build system deploys:

1. **phazevpn-portal.service** - Web portal (Flask/Gunicorn)
   - Location: `/opt/phaze-vpn/web-portal`
   - Port: 5000 (internal), 80/443 (via Nginx)

2. **phazevpn-protocol.service** - Python VPN protocol server
   - Location: `/opt/phaze-vpn/phazevpn-protocol`
   - Port: 51820/udp

3. **phazevpn-protocol-go.service** - Go VPN protocol server
   - Location: `/opt/phaze-vpn/phazevpn-protocol-go`
   - Port: 51820/udp

## Post-Deployment Configuration

### 1. Generate Certificates

```bash
cd /opt/phaze-vpn
sudo ./generate-certs.sh
```

### 2. Configure Web Portal

Edit `/opt/phaze-vpn/web-portal/app.py` or use environment variables:

```bash
export VPN_SERVER_IP=your-vps-ip
export VPN_SERVER_PORT=1194
export HTTPS_ENABLED=true
```

### 3. Start Services

```bash
# Enable services
sudo systemctl enable phazevpn-portal
sudo systemctl enable phazevpn-protocol

# Start services
sudo systemctl start phazevpn-portal
sudo systemctl start phazevpn-protocol

# Check status
sudo systemctl status phazevpn-portal
sudo systemctl status phazevpn-protocol
```

### 4. Setup SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d yourdomain.com
```

### 5. Configure Firewall

The deployment script automatically configures UFW, but verify:

```bash
sudo ufw status
sudo ufw allow 1194/udp
sudo ufw allow 51820/udp
```

## Troubleshooting

### Services won't start

Check logs:
```bash
sudo journalctl -u phazevpn-portal -f
sudo journalctl -u phazevpn-protocol -f
```

### Port already in use

Check what's using the port:
```bash
sudo netstat -tulpn | grep :5000
sudo netstat -tulpn | grep :1194
```

### Permission errors

Fix permissions:
```bash
sudo chown -R root:root /opt/phaze-vpn
sudo chmod 755 /opt/phaze-vpn
sudo chmod 600 /opt/phaze-vpn/certs/*.key
```

### Python dependencies missing

Install manually:
```bash
cd /opt/phaze-vpn/web-portal
sudo pip3 install -r requirements.txt
```

## Updating Services

To update after code changes:

```bash
# On VPS
cd /root/phaze-vpn
git pull  # or upload new files
sudo bash deploy-to-vps-cmake.sh
sudo systemctl restart phazevpn-portal phazevpn-protocol
```

## Manual Service Management

```bash
# Start
sudo systemctl start phazevpn-portal
sudo systemctl start phazevpn-protocol

# Stop
sudo systemctl stop phazevpn-portal
sudo systemctl stop phazevpn-protocol

# Restart
sudo systemctl restart phazevpn-portal
sudo systemctl restart phazevpn-protocol

# Status
sudo systemctl status phazevpn-portal
sudo systemctl status phazevpn-protocol

# Logs
sudo journalctl -u phazevpn-portal -f
sudo journalctl -u phazevpn-protocol -f
```

## Integration with Existing Scripts

The CMake build system works alongside existing deployment scripts:
- `DEPLOY-ALL-SERVICES.sh` - Can be run after CMake deployment
- `deploy-all-to-vps.sh` - Alternative deployment method
- Individual service deployment scripts

The CMake system provides a more structured, maintainable approach while maintaining compatibility.

