#!/usr/bin/env bash
PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SCRIPT="${PH_DIR}/31-setup-users-services.sh"

# -----------------------------------------------------------------
# Replace the existing download() with a safe version
# -----------------------------------------------------------------
sed -i '/^download() {/,$d' "$SCRIPT"   # delete old definition

sed -i '/^# 1️⃣ Install runit (tiny init system)$/a\
\
download() {\
    local url=$1\
    local file=$(basename "$url")\
    local dest="${PH_DIR}/sources/$file"\
    if [ -f "$dest" ]; then return; fi\
    echo "⬇️ Download $file (no‑cert, UA)..."\
    wget --no-check-certificate --user-agent="Mozilla/5.0 (PhazeOS build)" -q -O "$dest" "$url" || {\
        echo "❌ wget failed for $file" >&2; exit 1;\
    }\
    # Verify we got a real archive (gzip or xz) \
    if ! file "$dest" | grep -qE "gzip compressed data|XZ compressed data"; then\
        echo "❌ $file is not a valid archive (got HTML?)" >&2; rm -f "$dest"; exit 1;\
    fi\
}\
' "$SCRIPT"

# -----------------------------------------------------------------
# Ensure we rename the runit tarball to a stable name
# -----------------------------------------------------------------
sed -i '/^download "https:\/\/github.com\/justinmk\/runit\/archive\/refs\/tags\/v2.1.2.tar.gz"/c\
download "https://github.com/justinmk/runit/archive/refs/tags/v2.1.2.tar.gz"' "$SCRIPT"

sed -i '/^cd "$PH_DIR"$/a\
RUNIT_TAR="runit-2.1.2.tar.gz"\
mv "$PH_DIR/sources/v2.1.2.tar.gz" "$PH_DIR/sources/$RUNIT_TAR"\
' "$SCRIPT"

# Update the tar extraction line to use the new variable
sed -i 's|tar -xf "$PH_DIR/sources/v2.1.2.tar.gz"|tar -xf "$PH_DIR/sources/$RUNIT_TAR"|g' "$SCRIPT"

echo "✅ patch applied"
