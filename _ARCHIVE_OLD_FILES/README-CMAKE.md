# PhazeVPN CMake Build System

This project now includes a comprehensive CMake build system for building all services and components.

## Quick Start

### Prerequisites

```bash
# Install CMake
sudo apt-get update
sudo apt-get install cmake build-essential

# Install Go (for protocol server)
sudo apt-get install golang-go

# Install Python dependencies
sudo apt-get install python3 python3-pip python3-venv
```

### Building

```bash
# Build everything (local install)
./build.sh

# Build and install to system
./build.sh --install-system
sudo cmake --install build/

# Build specific components only
./build.sh --no-browser --no-protocol-go

# Clean build
./build.sh --clean
```

### Manual Build

```bash
mkdir build
cd build
cmake ..
cmake --build . -j$(nproc)
cmake --install .
```

## Build Options

Configure with CMake options:

- `BUILD_PROTOCOL_GO` - Build Go-based protocol server (default: ON)
- `BUILD_WEB_PORTAL` - Build web portal service (default: ON)
- `BUILD_PROTOCOL_PYTHON` - Build Python protocol service (default: ON)
- `BUILD_BROWSER` - Build PhazeBrowser (default: ON)
- `INSTALL_SYSTEMD_SERVICES` - Generate systemd service files (default: ON)
- `INSTALL_TO_SYSTEM` - Install to system directories (default: OFF)

Example:
```bash
cmake -DBUILD_BROWSER=OFF -DINSTALL_TO_SYSTEM=ON ..
```

## Project Structure

```
secure-vpn/
├── CMakeLists.txt              # Root CMake configuration
├── build.sh                    # Build script
├── phazevpn-protocol-go/
│   └── CMakeLists.txt          # Go protocol server
├── web-portal/
│   └── CMakeLists.txt          # Web portal service
├── phazevpn-protocol/
│   └── CMakeLists.txt          # Python protocol service
├── browser/
│   └── CMakeLists.txt          # Browser application
└── cmake/
    └── SystemdService.cmake   # Systemd service generation module
```

## Services Built

### 1. PhazeVPN Protocol Server (Go)
- Location: `phazevpn-protocol-go/`
- Builds: `phazevpn-server-go` binary
- Dependencies: Go 1.21+

### 2. Web Portal
- Location: `web-portal/`
- Service: Flask application with Gunicorn
- Dependencies: Python 3, Flask, Gunicorn

### 3. PhazeVPN Protocol Server (Python)
- Location: `phazevpn-protocol/`
- Service: Python-based VPN protocol server
- Dependencies: Python 3, cryptography

### 4. PhazeBrowser
- Location: `browser/` (or root `phazebrowser.py`)
- Application: GTK/WebKit2 browser with VPN integration
- Dependencies: Python 3, PyGObject, GTK3

## Systemd Services

The build system automatically generates systemd service files:

- `phazevpn-portal.service` - Web portal service
- `phazevpn-protocol.service` - Python protocol server
- `phazevpn-protocol-go.service` - Go protocol server

To install and enable services:

```bash
# After installing to system
sudo systemctl daemon-reload
sudo systemctl enable phazevpn-portal
sudo systemctl enable phazevpn-protocol
sudo systemctl start phazevpn-portal
sudo systemctl start phazevpn-protocol
```

## Installation Locations

### Local Install (default)
- Prefix: `build/install/`
- Services: `build/systemd/`

### System Install
- Prefix: `/opt/phaze-vpn/`
- Services: `/etc/systemd/system/`

## Development

### Adding a New Service

1. Create `CMakeLists.txt` in your service directory
2. Add `add_subdirectory(your-service)` to root `CMakeLists.txt`
3. Use `create_systemd_service()` in `cmake/SystemdService.cmake` for systemd integration

### Building Individual Components

```bash
# Build only Go protocol server
cmake --build build --target phazevpn-protocol-go-build

# Install only web portal
cmake --install build --component web-portal
```

## Troubleshooting

### CMake not found
```bash
sudo apt-get install cmake
```

### Go not found
```bash
sudo apt-get install golang-go
# Or disable Go build: ./build.sh --no-protocol-go
```

### Python dependencies missing
```bash
pip3 install -r web-portal/requirements.txt
pip3 install -r phazevpn-protocol/requirements.txt
```

### Build errors
```bash
# Clean and rebuild
./build.sh --clean
```

## Integration with Existing Build Scripts

The CMake build system works alongside existing build scripts:
- `build-deb.sh` - Debian package building
- `build-all-platforms.sh` - Cross-platform builds
- Individual service build scripts

CMake provides a unified build interface while maintaining compatibility with existing tooling.

