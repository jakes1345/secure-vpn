#!/bin/bash
# PhazeOS - Phase 3.3: Wlroots & Font Core
# Builds: gperf(host), xz, freetype, fontconfig, hwdata, libdisplay-info, libliftoff, wlroots

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
target="x86_64-phazeos-linux-gnu"
export PATH=$PHAZEOS/toolchain/bin:$HOME/.local/bin:$PATH
# We set CC/CXX later for cross-compilation, but first we might need host tools.

export PKG_CONFIG=$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config
export PKG_CONFIG_PATH=$PHAZEOS/usr/lib/pkgconfig:$PHAZEOS/usr/share/pkgconfig

echo "=========================================="
echo "  PHASE 3.3: WLROOTS & FONT CORE"
echo "=========================================="

mkdir -p $SOURCES

download() {
    local url=$1
    local file=$(basename $url)
    if [ ! -f "$SOURCES/$file" ]; then
        echo "⬇️ Downloading $file..."
        wget -q -O "$SOURCES/$file" "$url"
    fi
}

GPERF_VER="3.1"
XZ_VER="5.4.6"
FREETYPE_VER="2.13.2"
FONTCONFIG_VER="2.15.0"
HWDATA_VER="0.379"
LIBDISPLAY_INFO_VER="0.1.1"
LIBLIFTOFF_VER="0.4.1"
WLROOTS_VER="0.17.1" 

echo "📦 Downloading sources..."
download "http://ftp.gnu.org/pub/gnu/gperf/gperf-$GPERF_VER.tar.gz"
download "https://github.com/tukaani-project/xz/releases/download/v$XZ_VER/xz-$XZ_VER.tar.gz"
download "https://download.savannah.gnu.org/releases/freetype/freetype-$FREETYPE_VER.tar.xz"
download "https://www.freedesktop.org/software/fontconfig/release/fontconfig-$FONTCONFIG_VER.tar.xz"
download "https://github.com/vcrhonek/hwdata/archive/refs/tags/v$HWDATA_VER.tar.gz"
mv $SOURCES/v$HWDATA_VER.tar.gz $SOURCES/hwdata-$HWDATA_VER.tar.gz 2>/dev/null || true
download "https://gitlab.freedesktop.org/emersion/libdisplay-info/-/releases/$LIBDISPLAY_INFO_VER/downloads/libdisplay-info-$LIBDISPLAY_INFO_VER.tar.xz"
download "https://gitlab.freedesktop.org/emersion/libliftoff/-/releases/v$LIBLIFTOFF_VER/downloads/libliftoff-$LIBLIFTOFF_VER.tar.gz"
download "https://gitlab.freedesktop.org/wlroots/wlroots/-/releases/$WLROOTS_VER/downloads/wlroots-$WLROOTS_VER.tar.gz"

# 0. Gperf (Host Tool - needed by fontconfig)
echo "🔨 Building Gperf (Host)..."
cd $BUILD
rm -rf gperf-$GPERF_VER
tar -xf $SOURCES/gperf-$GPERF_VER.tar.gz
cd gperf-$GPERF_VER
# Force host compiler
./configure --prefix=$PHAZEOS/toolchain CC=gcc CXX=g++
make -j$(nproc)
make install

# NOW set cross-compilation environment
export CC=$target-gcc
export CXX=$target-g++
export AR=$target-ar
export RANLIB=$target-ranlib

# 0b. XZ Utils (Liblzma)
echo "🔨 Building XZ Utils..."
cd $BUILD
rm -rf xz-$XZ_VER
tar -xf $SOURCES/xz-$XZ_VER.tar.gz
cd xz-$XZ_VER
./configure --host=$target --prefix=/usr --disable-static --disable-doc --disable-nls
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 0c. CLEANUP .LA FILES (Crucial fix for Libtool Cross-Compile issues)
echo "🧹 Removing .la files to prevent Libtool linking errors..."
rm -f $PHAZEOS/usr/lib/*.la
rm -f $PHAZEOS/lib/*.la

# 1. Freetype
echo "🔨 Building Freetype..."
cd $BUILD
rm -rf freetype-$FREETYPE_VER
tar -xf $SOURCES/freetype-$FREETYPE_VER.tar.xz
cd freetype-$FREETYPE_VER
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt \
    -Dpng=disabled -Dharfbuzz=disabled -Dbrotli=disabled -Dbzip2=disabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 2. Fontconfig
echo "🔨 Building Fontconfig..."
cd $BUILD
rm -rf fontconfig-$FONTCONFIG_VER
tar -xf $SOURCES/fontconfig-$FONTCONFIG_VER.tar.xz
cd fontconfig-$FONTCONFIG_VER
# Manually patch needed? Likely PATH_MAX check.
find . -name "*.c" -exec sed -i '1i #include <limits.h>\n#include <linux/limits.h>\n#ifndef PATH_MAX\n#define PATH_MAX 4096\n#endif' {} +
# Disable docs, tests, and NLS.
./configure --host=$target --prefix=/usr --disable-docs --disable-nls --enable-libxml2 --with-sysroot=$PHAZEOS
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 3. hwdata (Hardware Identification Data)
echo "🔨 Building hwdata..."
cd $BUILD
rm -rf hwdata-$HWDATA_VER
tar -xf $SOURCES/hwdata-$HWDATA_VER.tar.gz
cd hwdata-$HWDATA_VER
./configure --prefix=/usr
make
make DESTDIR=$PHAZEOS install

# 4. libdisplay-info (EDID parsing for Wayland)
echo "🔨 Building libdisplay-info..."
cd $BUILD
rm -rf libdisplay-info-$LIBDISPLAY_INFO_VER
tar -xf $SOURCES/libdisplay-info-$LIBDISPLAY_INFO_VER.tar.xz
cd libdisplay-info-$LIBDISPLAY_INFO_VER
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 5. libliftoff (KMS Plane offloading - Good for performance)
echo "🔨 Building libliftoff..."
cd $BUILD
rm -rf libliftoff-$LIBLIFTOFF_VER
tar -xf $SOURCES/libliftoff-$LIBLIFTOFF_VER.tar.gz
cd libliftoff-$LIBLIFTOFF_VER
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 6. wlroots (The Wayland Compositor Library)
echo "🔨 Building wlroots..."
cd $BUILD
rm -rf wlroots-$WLROOTS_VER
tar -xf $SOURCES/wlroots-$WLROOTS_VER.tar.gz
cd wlroots-$WLROOTS_VER
# Aggressively patch PATH_MAX here too just in case
find . -name "*.c" -exec sed -i '1i #include <limits.h>\n#include <linux/limits.h>\n#ifndef PATH_MAX\n#define PATH_MAX 4096\n#endif' {} +
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt \
    -Dexamples=false -Dxcb-errors=disabled -Dxwayland=disabled \
    -Dbackends=drm,libinput -Drenderers=gles2
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

echo "✅ Wlroots & Core Built!"
echo "Rebuilding VDI..."
cd $PHAZEOS
./16-build-vdi-disk.sh
