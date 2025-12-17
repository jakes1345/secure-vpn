#!/usr/bin/env bash
PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SCRIPT="${PH_DIR}/30-build-desktop.sh"

# 1️⃣ Move the download() definition to the top (right after set -e)
sed -i '/^set -e$/a\
\
download() {\
    local url=$1\
    local file=$(basename "$url")\
    if [ ! -f "$SOURCES/$file" ]; then\
        echo "⬇️ Downloading $file..."\
        wget -q -O "$SOURCES/$file" "$url"\
    fi\
}' "$SCRIPT"

# 2️⃣ Remove the stray mv line (no rename needed)
sed -i '/mv "\$SOURCES\/v${LABWC_VER}.tar.gz"/d' "$SCRIPT"

# 3️⃣ Fix the Labwc extraction line to use the correct tarball name
sed -i 's|tar -xf $SOURCES/labwc-${LABWC_VER}.tar.gz|tar -xf $SOURCES/labwc-0.7.0.tar.gz|' "$SCRIPT"
