# PhazeVPN Build Guide

## What Was Added

A complete CMake build system has been added to the project with:

### ✅ CMakeLists.txt Files
- **Root** (`CMakeLists.txt`) - Main build configuration
- **phazevpn-protocol-go/CMakeLists.txt** - Go protocol server build
- **web-portal/CMakeLists.txt** - Web portal service build  
- **phazevpn-protocol/CMakeLists.txt** - Python protocol service build
- **browser/CMakeLists.txt** - Browser application build

### ✅ Build Infrastructure
- **build.sh** - Convenient build script with options
- **cmake/SystemdService.cmake** - Systemd service file generation
- **README-CMAKE.md** - Comprehensive CMake documentation

### ✅ Services Configured
1. **PhazeVPN Protocol Server (Go)** - Native Go VPN server
2. **Web Portal** - Flask/Gunicorn web interface
3. **PhazeVPN Protocol (Python)** - Python VPN protocol server
4. **PhazeBrowser** - GTK/WebKit2 browser with VPN

## Quick Start

```bash
# Build everything
./build.sh

# Build and install to system
./build.sh --install-system
sudo cmake --install build/

# Build specific components
./build.sh --no-browser --no-protocol-go

# Clean build
./build.sh --clean
```

## What This Fixes

Before: No unified build system, missing CMakeLists.txt files, no proper service management

After: 
- ✅ Complete CMake build system
- ✅ Systemd service file generation
- ✅ Dependency management
- ✅ Cross-platform build support
- ✅ Proper installation targets
- ✅ Build script with options

## Next Steps

1. **Test the build:**
   ```bash
   ./build.sh
   ```

2. **Install services:**
   ```bash
   ./build.sh --install-system
   sudo cmake --install build/
   sudo systemctl daemon-reload
   ```

3. **Enable services:**
   ```bash
   sudo systemctl enable phazevpn-portal
   sudo systemctl enable phazevpn-protocol
   sudo systemctl start phazevpn-portal
   ```

## Build Options

See `README-CMAKE.md` for full documentation of all CMake options and build targets.

