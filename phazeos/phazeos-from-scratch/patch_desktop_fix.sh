#!/usr/bin/env bash
PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SCRIPT="${PH_DIR}/30-build-desktop.sh"

# 1️⃣ Replace the download() function with a robust version (uses --no-check-certificate)
sed -i '/^download() {/,$d' "$SCRIPT"   # delete the old function and everything after it
sed -i '/^set -e$/a\
\
download() {\
    local url=$1\
    local file=$(basename "$url")\
    if [ ! -f "$SOURCES/$file" ]; then\
        echo "⬇️ Downloading $file (no‑cert check)..."\
        wget --no-check-certificate -q -O "$SOURCES/$file" "$url" || {\
            echo "❌ Failed to download $file – aborting." >&2;\
            exit 1;\
        }\
    fi\
}' "$SCRIPT"

# 2️⃣ Ensure the Labwc extraction uses the correct tarball variable
sed -i 's|tar -xf $SOURCES/labwc-$LABWC_VER.tar.gz|tar -xf $SOURCES/$LABWC_TAR|' "$SCRIPT"

# 3️⃣ Add a sanity check before extracting Labwc
sed -i '/^cd $BUILD$/a\
if [ ! -f "$SOURCES/$LABWC_TAR" ]; then\
    echo "❌ Labwc tarball $LABWC_TAR missing – aborting." >&2;\
    exit 1;\
fi' "$SCRIPT"
