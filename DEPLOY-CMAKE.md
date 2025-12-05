# Deploy PhazeVPN to VPS using CMake (Paramiko)

This script automatically uploads your PhazeVPN project to a VPS and builds it using CMake.

## Quick Start

```bash
# Set VPS credentials (or use defaults)
export VPS_HOST=your-vps-ip
export VPS_USER=root
export VPS_PASS=your-password

# Deploy
python3 deploy-cmake-to-vps.py
```

## What It Does

1. **Connects to VPS** via SSH (using SSH key or password)
2. **Uploads CMake build system** and all source files
3. **Installs dependencies** (CMake, Go, Python packages)
4. **Builds all services** using CMake on the VPS
5. **Installs to `/opt/phaze-vpn`** with systemd services

## Configuration

### Environment Variables

```bash
export VPS_HOST=15.204.11.19      # VPS IP address
export VPS_USER=root              # SSH username
export VPS_PASS=your-password     # SSH password (if not using keys)
export VPS_DIR=/root/phaze-vpn    # Source directory on VPS
```

### SSH Keys (Preferred)

The script will automatically try SSH keys from:
- `~/.ssh/id_rsa`
- `~/.ssh/id_ed25519`
- `~/.ssh/id_ecdsa`

If no key is found, it falls back to password authentication.

## Files Uploaded

- **CMake build system**: `CMakeLists.txt`, `build.sh`, `deploy-to-vps-cmake.sh`
- **CMake modules**: `cmake/SystemdService.cmake`
- **Service CMakeLists**: All `*/CMakeLists.txt` files
- **Source code**: Web portal, protocol servers, configs, scripts
- **Documentation**: README files

## Excluded Files

The script automatically excludes:
- Build artifacts (`build/`, `dist/`, `*.pyc`)
- Git files (`.git/`)
- Virtual environments (`venv/`, `.venv/`)
- Logs and temp files (`*.log`, `*.tmp`)
- Node modules (`node_modules/`)

## After Deployment

The script will show you next steps. Typically:

```bash
# SSH to VPS
ssh root@your-vps-ip

# Enable services
sudo systemctl enable phazevpn-portal phazevpn-protocol

# Start services
sudo systemctl start phazevpn-portal phazevpn-protocol

# Check status
sudo systemctl status phazevpn-portal
sudo journalctl -u phazevpn-portal -f
```

## Troubleshooting

### Connection Failed
- Check VPS IP and credentials
- Ensure SSH is enabled on VPS
- Try password authentication if keys don't work

### Upload Failed
- Check disk space on VPS
- Verify file permissions
- Check network connectivity

### Build Failed
- Check VPS has enough resources
- Verify all dependencies installed
- Check build logs: `cd /root/phaze-vpn/build-vps && cat CMakeCache.txt`

### Services Not Starting
- Check logs: `sudo journalctl -u phazevpn-portal -n 50`
- Verify installation: `ls -la /opt/phaze-vpn`
- Check permissions: `sudo chown -R root:root /opt/phaze-vpn`

## Manual Steps

If automatic deployment fails, you can manually:

1. **Upload files manually:**
   ```bash
   scp -r . root@vps-ip:/root/phaze-vpn/
   ```

2. **SSH and build:**
   ```bash
   ssh root@vps-ip
   cd /root/phaze-vpn
   sudo bash deploy-to-vps-cmake.sh
   ```

## Integration

This script works alongside:
- `deploy-to-vps-cmake.sh` - Build script run on VPS
- `build-and-deploy-vps.sh` - Local build and package
- Existing `deploy-*-vps.py` scripts - Individual service deployment

