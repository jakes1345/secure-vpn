#!/bin/bash
# 🚀 Build and Deploy to VPS Script
# Builds locally and prepares for VPS deployment
# Run this LOCALLY, then upload to VPS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build-vps-deploy"
VPS_USER="${VPS_USER:-root}"
VPS_HOST="${VPS_HOST:-your-vps-ip}"
VPS_PATH="${VPS_PATH:-/root/phaze-vpn}"

echo "=========================================="
echo "🚀 Build and Deploy to VPS"
echo "=========================================="
echo ""
echo "VPS: ${VPS_USER}@${VPS_HOST}"
echo "Path: ${VPS_PATH}"
echo ""

# Check for CMake
if ! command -v cmake &> /dev/null; then
    echo "❌ Error: CMake is not installed"
    echo "Install with: sudo apt-get install cmake"
    exit 1
fi

# Create deployment build directory
echo "🔨 Creating build directory..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Configure CMake for deployment build
echo "⚙️  Configuring CMake..."
cmake "${SCRIPT_DIR}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DINSTALL_TO_SYSTEM=OFF \
    -DBUILD_PROTOCOL_GO=ON \
    -DBUILD_WEB_PORTAL=ON \
    -DBUILD_PROTOCOL_PYTHON=ON \
    -DBUILD_BROWSER=ON \
    -DINSTALL_SYSTEMD_SERVICES=ON

# Build
echo ""
echo "🔨 Building..."
cmake --build . --config Release -j$(nproc)

# Install to local directory
echo ""
echo "📦 Installing to deployment directory..."
cmake --install . --prefix "${BUILD_DIR}/install"

# Create deployment archive
echo ""
echo "📦 Creating deployment archive..."
cd "${BUILD_DIR}/install"
tar czf "${SCRIPT_DIR}/phazevpn-vps-deploy.tar.gz" .

# Create deployment script
cat > "${SCRIPT_DIR}/deploy-on-vps.sh" << 'DEPLOY_SCRIPT'
#!/bin/bash
# Deployment script to run ON THE VPS
# Extracts and installs PhazeVPN

set -e

VPS_INSTALL_DIR="/opt/phaze-vpn"
ARCHIVE="phazevpn-vps-deploy.tar.gz"

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "=========================================="
echo "🚀 Installing PhazeVPN on VPS"
echo "=========================================="
echo ""

# Extract archive
if [ ! -f "${ARCHIVE}" ]; then
    echo "❌ Error: ${ARCHIVE} not found!"
    exit 1
fi

echo "📦 Extracting files..."
mkdir -p "${VPS_INSTALL_DIR}"
tar xzf "${ARCHIVE}" -C "${VPS_INSTALL_DIR}"

# Set permissions
echo "🔐 Setting permissions..."
chown -R root:root "${VPS_INSTALL_DIR}"
chmod 755 "${VPS_INSTALL_DIR}"

# Install systemd services
if [ -d "${VPS_INSTALL_DIR}/systemd" ]; then
    echo "🔧 Installing systemd services..."
    cp "${VPS_INSTALL_DIR}"/systemd/*.service /etc/systemd/system/
    systemctl daemon-reload
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    if [ -f "${VPS_INSTALL_DIR}/web-portal/requirements.txt" ]; then
        pip3 install -r "${VPS_INSTALL_DIR}/web-portal/requirements.txt"
    fi
    if [ -f "${VPS_INSTALL_DIR}/phazevpn-protocol/requirements.txt" ]; then
        pip3 install -r "${VPS_INSTALL_DIR}/phazevpn-protocol/requirements.txt"
    fi
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure services: cd ${VPS_INSTALL_DIR}"
echo "2. Enable services: sudo systemctl enable phazevpn-portal phazevpn-protocol"
echo "3. Start services: sudo systemctl start phazevpn-portal phazevpn-protocol"
echo ""
DEPLOY_SCRIPT

chmod +x "${SCRIPT_DIR}/deploy-on-vps.sh"

echo ""
echo "✅ Build and packaging complete!"
echo ""
echo "Files created:"
echo "  - ${SCRIPT_DIR}/phazevpn-vps-deploy.tar.gz"
echo "  - ${SCRIPT_DIR}/deploy-on-vps.sh"
echo ""
echo "To deploy to VPS:"
echo "1. Upload files:"
echo "   scp phazevpn-vps-deploy.tar.gz deploy-on-vps.sh ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/"
echo ""
echo "2. SSH to VPS and run:"
echo "   ssh ${VPS_USER}@${VPS_HOST}"
echo "   cd ${VPS_PATH}"
echo "   sudo bash deploy-on-vps.sh"
echo ""

