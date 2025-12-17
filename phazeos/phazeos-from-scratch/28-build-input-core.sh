#!/bin/bash
# PhazeOS - Phase 3.2: Input & Core Libs
# Builds: libudev-zero, xkeyboard-config, libxkbcommon, libevdev, mtdev, libinput, pixman, seatd

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
target="x86_64-phazeos-linux-gnu"
export PATH=$PHAZEOS/toolchain/bin:$HOME/.local/bin:$PATH
export CC=$target-gcc
export CXX=$target-g++
export AR=$target-ar
export RANLIB=$target-ranlib
export PKG_CONFIG=$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config
export PKG_CONFIG_PATH=$PHAZEOS/usr/lib/pkgconfig:$PHAZEOS/usr/share/pkgconfig

echo "=========================================="
echo "  PHASE 3.2: INPUT & CORE LIBS"
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

# Versions
LIBUDEV_ZERO_VER="1.0.3"
XKB_CONFIG_VER="2.41"
LIBXKBCOMMON_VER="1.6.0"
LIBEVDEV_VER="1.13.1"
MTDEV_VER="1.1.6"
LIBINPUT_VER="1.25.0"
PIXMAN_VER="0.43.2"
SEATD_VER="0.8.0"

echo "📦 Downloading sources..."
download "https://github.com/illiliti/libudev-zero/archive/refs/tags/$LIBUDEV_ZERO_VER.tar.gz"
mv $SOURCES/$LIBUDEV_ZERO_VER.tar.gz $SOURCES/libudev-zero-$LIBUDEV_ZERO_VER.tar.gz 2>/dev/null || true
download "https://www.x.org/archive/individual/data/xkeyboard-config/xkeyboard-config-$XKB_CONFIG_VER.tar.xz"
download "https://xkbcommon.org/download/libxkbcommon-$LIBXKBCOMMON_VER.tar.xz"
download "https://www.freedesktop.org/software/libevdev/libevdev-$LIBEVDEV_VER.tar.xz"
download "https://bitmath.org/code/mtdev/mtdev-$MTDEV_VER.tar.bz2"
download "https://gitlab.freedesktop.org/libinput/libinput/-/archive/$LIBINPUT_VER/libinput-$LIBINPUT_VER.tar.gz"
download "https://www.cairographics.org/releases/pixman-$PIXMAN_VER.tar.gz"
download "https://git.sr.ht/~kennylevinsen/seatd/archive/$SEATD_VER.tar.gz"
mv $SOURCES/$SEATD_VER.tar.gz $SOURCES/seatd-$SEATD_VER.tar.gz 2>/dev/null || true

# Common patch string for PATH_MAX/LINE_MAX
PATCH_CMD="1i #include <limits.h>\n#include <linux/limits.h>\n#ifndef PATH_MAX\n#define PATH_MAX 4096\n#endif\n#ifndef LINE_MAX\n#define LINE_MAX 2048\n#endif"

# 0. libudev-zero (Simple libudev implementation for libinput)
echo "🔨 Building libudev-zero..."
cd $BUILD
rm -rf libudev-zero-$LIBUDEV_ZERO_VER
tar -xf $SOURCES/libudev-zero-$LIBUDEV_ZERO_VER.tar.gz
cd libudev-zero-$LIBUDEV_ZERO_VER
# Patch sources
find . -name "*.c" -exec sed -i "$PATCH_CMD" {} +
make CC=$target-gcc AR=$target-ar
make install PREFIX=$PHAZEOS/usr

# 1. xkeyboard-config (Data)
echo "🔨 Building xkeyboard-config..."
cd $BUILD
rm -rf xkeyboard-config-$XKB_CONFIG_VER
tar -xf $SOURCES/xkeyboard-config-$XKB_CONFIG_VER.tar.xz
cd xkeyboard-config-$XKB_CONFIG_VER
# Modern xkeyboard-config uses meson
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt -Dnls=false
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 2. libxkbcommon
echo "🔨 Building libxkbcommon..."
cd $BUILD
rm -rf libxkbcommon-$LIBXKBCOMMON_VER
tar -xf $SOURCES/libxkbcommon-$LIBXKBCOMMON_VER.tar.xz
cd libxkbcommon-$LIBXKBCOMMON_VER
# Patch LONG_BIT using a specific command as it needs a specific value
find . -name "*.c" -exec sed -i '1i #define LONG_BIT 64' {} +
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt \
    -Denable-x11=false -Denable-docs=false -Denable-wayland=true -Denable-tools=false
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 3. libevdev
echo "🔨 Building libevdev..."
cd $BUILD
rm -rf libevdev-$LIBEVDEV_VER
tar -xf $SOURCES/libevdev-$LIBEVDEV_VER.tar.xz
cd libevdev-$LIBEVDEV_VER
# Patch sources
find . -name "*.c" -exec sed -i "$PATCH_CMD" {} +
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt \
    -Dtests=disabled -Ddocumentation=disabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 4. mtdev (Multitouch Protocol)
echo "🔨 Building mtdev..."
cd $BUILD
rm -rf mtdev-$MTDEV_VER
tar -xf $SOURCES/mtdev-$MTDEV_VER.tar.bz2
cd mtdev-$MTDEV_VER
# Patch sources
find . -name "*.c" -exec sed -i "$PATCH_CMD" {} +
./configure --host=$target --prefix=/usr --disable-static
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 5. Pixman (Pixel Manipulation)
echo "🔨 Building Pixman..."
cd $BUILD
rm -rf pixman-$PIXMAN_VER
tar -xf $SOURCES/pixman-$PIXMAN_VER.tar.gz
cd pixman-$PIXMAN_VER
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt \
    -Dtests=disabled -Dgtk=disabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 6. libinput (The big one)
echo "🔨 Building libinput..."
cd $BUILD
rm -rf libinput-$LIBINPUT_VER
tar -xf $SOURCES/libinput-$LIBINPUT_VER.tar.gz
cd libinput-$LIBINPUT_VER
# Patch sources
find . -name "*.c" -exec sed -i "$PATCH_CMD" {} +
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt \
    -Dtests=false -Ddocumentation=false -Ddebug-gui=false \
    -Dlibwacom=false
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 7. seatd (Seat Management)
echo "🔨 Building seatd..."
cd $BUILD
rm -rf seatd-$SEATD_VER
tar -xf $SOURCES/seatd-$SEATD_VER.tar.gz
cd seatd-$SEATD_VER
# Patch sources
find . -name "*.c" -exec sed -i "$PATCH_CMD" {} +
meson setup build --prefix=/usr --cross-file ../wayland-1.22.0/cross_file.txt \
    -Dlibseat-seatd=enabled -Dlibseat-logind=disabled -Dlibseat-builtin=enabled \
    -Dserver=enabled -Dexamples=disabled -Dman-pages=disabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

echo "✅ Input & Core Libs Built!"
echo "Rebuilding VDI..."
cd $PHAZEOS
./16-build-vdi-disk.sh
