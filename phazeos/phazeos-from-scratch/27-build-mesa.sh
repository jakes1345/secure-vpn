#!/bin/bash
# PhazeOS - Phase 3.1: 3D Graphics (Mesa)
# Builds LLVM (Required for Mesa) and Mesa 3D Drivers

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
export PKG_CONFIG_PATH=$PHAZEOS/usr/lib/pkgconfig:$PHAZEOS/usr/share/pkgconfig

# IMPORTANT: Ensure our custom cross-pkg-config is used for Meson
export PKG_CONFIG=$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config

# Versions
MESA_VER="23.1.9"
LIBDRM_VER="2.4.120"
LLVM_VER="17.0.6" # Not used

echo "=========================================="
echo "  PHASE 3.1: 3D GRAPHICS (MESA)"
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

echo "📦 Downloading sources..."
download "https://dri.freedesktop.org/libdrm/libdrm-$LIBDRM_VER.tar.xz"
download "https://archive.mesa3d.org/mesa-$MESA_VER.tar.xz"
# 2. LLVM - SKIPPED (Using softpipe for software rasterization to avoid complex LLVM cross-compile)

# 3. Mesa 3D
echo "🔨 Building Mesa 3D..."
cd $BUILD
rm -rf mesa-$MESA_VER
tar -xf $SOURCES/mesa-$MESA_VER.tar.xz
cd mesa-$MESA_VER

# Patch: Fix PATH_MAX/NAME_MAX undeclared
find . -name "*.c" -exec sed -i '1i #include <limits.h>\n#include <linux/limits.h>\n#ifndef PATH_MAX\n#define PATH_MAX 4096\n#endif\n#ifndef NAME_MAX\n#define NAME_MAX 255\n#endif' {} +

meson setup build --prefix=/usr \
    --cross-file ../wayland-1.22.0/cross_file.txt \
    -Dplatforms=wayland \
    -Dgallium-drivers=swrast,virgl \
    -Dvulkan-drivers=[] \
    -Dllvm=disabled \
    -Dshared-llvm=disabled \
    -Dgles1=disabled \
    -Dgles2=enabled \
    -Dopengl=true \
    -Dglx=disabled \
    -Dgbm=enabled \
    -Dtools=[] \
    -Dbuildtype=release

ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

echo "✅ 3D Graphics Stack Built!"
echo "Rebuilding VDI..."
cd $PHAZEOS
./16-build-vdi-disk.sh
