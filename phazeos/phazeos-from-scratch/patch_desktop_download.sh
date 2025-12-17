#!/usr/bin/env bash
PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SCRIPT="${PH_DIR}/30-build-desktop.sh"

# Replace old download() with robust version (User-Agent, cert ignore, validation)
sed -i '/^download() {/,$d' "$SCRIPT"

sed -i '/^set -e$/a\
\
download() {\
    local url="$1"\
    local file=$(basename "$url")\
    local dest="$SOURCES/$file"\
    if [ -f "$dest" ]; then return; fi\
    echo "⬇️ Downloading $file (no‑cert, UA)..."\
    wget --no-check-certificate --user-agent="Mozilla/5.0 (PhazeOS build)" -q -O "$dest" "$url" || {\
        echo "❌ wget failed for $file" >&2; exit 1;\
    }\
    # Verify we got a real archive (gzip or xz)\
    if ! file "$dest" | grep -qE "gzip compressed data|XZ compressed data"; then\
        echo "❌ $file is not a valid archive (got HTML?)" >&2; rm -f "$dest"; exit 1;\
    fi\
}\
' "$SCRIPT"

# Ensure Labwc extraction uses the correct variable
sed -i 's|tar -xf $SOURCES/labwc-$LABWC_VER.tar.gz|tar -xf $SOURCES/$LABWC_TAR|' "$SCRIPT"

# Add sanity check before extracting Labwc
sed -i '/^cd $BUILD$/a\
if [ ! -f "$SOURCES/$LABWC_TAR" ]; then\
    echo "❌ Labwc tarball $LABWC_TAR missing – aborting." >&2; exit 1;\
fi' "$SCRIPT"

echo "✅ Patch applied – robust download ready."
