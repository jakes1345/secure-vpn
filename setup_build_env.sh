#!/bin/bash
# Setup PhazeOS Build Environment
# Installs Docker and prepares directories

echo "🏗️  Setting up PhazeOS Factory..."

# 1. Install Docker if missing
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-buildx
    sudo usermod -aG docker $USER
    echo "✅ Docker Installed. You might need to LOG OUT and LOG BACK IN for permissions to take effect."
    echo "⚠️  If the build script fails with 'permission denied', run: sudo chmod 666 /var/run/docker.sock"
else
    echo "✅ Docker is already installed."
fi

# 2. Create Build Directory
mkdir -p phazeos-build
cd phazeos-build

# 3. Create Dockerfile for the Builder
cat > Dockerfile << EOF
FROM archlinux:latest
RUN pacman -Syu --noconfirm archiso git make
WORKDIR /build
CMD ["/bin/bash"]
EOF

echo "✅ Build Environment Ready in ./phazeos-build/"
echo "Run './build_phazeos_iso.sh' to start cooking."
