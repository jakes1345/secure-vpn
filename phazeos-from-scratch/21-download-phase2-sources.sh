#!/bin/bash
# PhazeOS - Phase 2 Source Download
# Downloads networking, security, and editor packages.

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources

mkdir -p $SOURCES
cd $SOURCES

echo "=========================================="
echo "  DOWNLOADING PHASE 2 SOURCES"
echo "=========================================="

download() {
    local URL=$1
    local FILE=$(basename "$URL")
    if [ -f "$FILE" ]; then
        echo "✅ $FILE already exists."
    else
        echo "⬇️  Downloading $FILE..."
        wget "$URL" || { echo "❌ Failed to download $FILE"; exit 1; }
    fi
}

# 1. OpenSSL (Security)
download "https://www.openssl.org/source/openssl-3.2.1.tar.gz"

# 2. IPRoute2 (Networking)
download "https://mirrors.edge.kernel.org/pub/linux/utils/net/iproute2/iproute2-6.7.0.tar.xz"

# 3. DHCPCD (DHCP Client)
download "https://github.com/NetworkConfiguration/dhcpcd/releases/download/v10.0.6/dhcpcd-10.0.6.tar.xz"

# 4. Nano (Text Editor)
download "https://www.nano-editor.org/dist/v7/nano-7.2.tar.xz"

# 5. Procps-ng (Process Monitor)
download "https://sourceforge.net/projects/procps-ng/files/Production/procps-ng-4.0.4.tar.xz"

# 6. Zlib (Compression dependency for OpenSSL/OpenSSH)
download "https://zlib.net/zlib-1.3.1.tar.gz"

echo ""
echo "✅ Phase 2 Downloads Complete!"
