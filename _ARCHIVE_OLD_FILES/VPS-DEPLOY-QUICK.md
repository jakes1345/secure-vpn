# Quick VPS Deployment Guide

## On Your VPS

```bash
# 1. Upload the project (or clone it)
cd /root
git clone <your-repo> phaze-vpn
# OR upload via scp/rsync

# 2. Run the CMake deployment script
cd phaze-vpn
sudo bash deploy-to-vps-cmake.sh
```

That's it! The script will:
- ✅ Install all dependencies (CMake, Go, Python packages)
- ✅ Build all services
- ✅ Install to `/opt/phaze-vpn`
- ✅ Configure systemd services
- ✅ Setup firewall and networking

## After Deployment

```bash
# Enable and start services
sudo systemctl enable phazevpn-portal phazevpn-protocol
sudo systemctl start phazevpn-portal phazevpn-protocol

# Check status
sudo systemctl status phazevpn-portal
sudo systemctl status phazevpn-protocol

# View logs
sudo journalctl -u phazevpn-portal -f
sudo journalctl -u phazevpn-protocol -f
```

## What Gets Installed

- **Web Portal**: `/opt/phaze-vpn/web-portal` (port 5000, proxied via Nginx)
- **Protocol Server (Python)**: `/opt/phaze-vpn/phazevpn-protocol` (port 51820)
- **Protocol Server (Go)**: `/opt/phaze-vpn/phazevpn-protocol-go` (port 51820)
- **Systemd Services**: `/etc/systemd/system/phazevpn-*.service`

## Troubleshooting

```bash
# Check if services are running
sudo systemctl list-units | grep phazevpn

# Check logs
sudo journalctl -u phazevpn-portal --no-pager -l
sudo journalctl -u phazevpn-protocol --no-pager -l

# Restart services
sudo systemctl restart phazevpn-portal phazevpn-protocol
```

