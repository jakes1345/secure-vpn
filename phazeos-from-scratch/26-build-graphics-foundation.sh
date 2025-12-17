#!/bin/bash
# PhazeOS - Phase 3: Graphics Foundation
# Builds LibFFI, Expat, LibXML2, Wayland, Wayland-Protocols

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
target="x86_64-phazeos-linux-gnu"
export PATH=$PHAZEOS/toolchain/bin:$PATH
export CC=$target-gcc
export CXX=$target-g++
export AR=$target-ar
export RANLIB=$target-ranlib
export PKG_CONFIG_PATH=$PHAZEOS/usr/lib/pkgconfig:$PHAZEOS/usr/share/pkgconfig

# Version Definitions
LIBFFI_VER="3.4.6"
EXPAT_VER="2.6.0"
LIBXML2_VER="2.12.5"
WAYLAND_VER="1.22.0"
WAYLAND_PROTOCOLS_VER="1.33"

echo "=========================================="
echo "  PHASE 3: GRAPHICS FOUNDATION"
echo "=========================================="

mkdir -p $SOURCES

# Helper to download if missing
download() {
    local url=$1
    local file=$(basename $url)
    if [ ! -f "$SOURCES/$file" ]; then
        echo "⬇️ Downloading $file..."
        wget -q -O "$SOURCES/$file" "$url"
    fi
}

echo "📦 Downloading sources..."
download "https://github.com/libffi/libffi/releases/download/v$LIBFFI_VER/libffi-$LIBFFI_VER.tar.gz"
download "https://github.com/libexpat/libexpat/releases/download/R_${EXPAT_VER//./_}/expat-$EXPAT_VER.tar.xz"
download "https://download.gnome.org/sources/libxml2/${LIBXML2_VER%.*}/libxml2-$LIBXML2_VER.tar.xz"
download "https://gitlab.freedesktop.org/wayland/wayland/-/releases/$WAYLAND_VER/downloads/wayland-$WAYLAND_VER.tar.xz"
download "https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/$WAYLAND_PROTOCOLS_VER/downloads/wayland-protocols-$WAYLAND_PROTOCOLS_VER.tar.xz"

# 1. LibFFI
echo "🔨 Building LibFFI..."
cd $BUILD
rm -rf libffi-$LIBFFI_VER
tar -xf $SOURCES/libffi-$LIBFFI_VER.tar.gz
cd libffi-$LIBFFI_VER
./configure --host=$target --prefix=/usr --disable-static
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 2. Expat (XML Parser)
echo "🔨 Building Expat..."
cd $BUILD
rm -rf expat-$EXPAT_VER
tar -xf $SOURCES/expat-$EXPAT_VER.tar.xz
cd expat-$EXPAT_VER
./configure --host=$target --prefix=/usr --disable-static
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 3. LibXML2
echo "🔨 Building LibXML2..."
cd $BUILD
rm -rf libxml2-$LIBXML2_VER
tar -xf $SOURCES/libxml2-$LIBXML2_VER.tar.xz
cd libxml2-$LIBXML2_VER
./configure --host=$target --prefix=/usr --disable-static --without-python
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 4. Wayland
echo "🔨 Building Wayland..."
cd $BUILD
rm -rf wayland-$WAYLAND_VER
tar -xf $SOURCES/wayland-$WAYLAND_VER.tar.xz
cd wayland-$WAYLAND_VER
# Wayland usually needs 'meson' but basic configure might exist on older versions or requires a wrap.
# Wait, standard Wayland uses Meson. I might not have meson/ninja in the toolchain.
# Checking if I can use host meson with a cross file.
# Since I haven't set up Meson, I'll use the 'configure' fallback if available OR
# I need to install Meson/Ninja on HOST to drive the build.

# Helper: Create pkg-config wrapper for cross-compilation
cat > $PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config <<EOF
#!/bin/bash
export PKG_CONFIG_DIR=
export PKG_CONFIG_LIBDIR=$PHAZEOS/usr/lib/pkgconfig:$PHAZEOS/usr/share/pkgconfig
export PKG_CONFIG_SYSROOT_DIR=$PHAZEOS
exec pkg-config "\$@"
EOF
chmod +x $PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config

# Assuming host has meson/ninja. Creating cross-file.
# IMPORTANT: Use absolute paths to avoid 'command not found' errors in Ninja
cat > cross_file.txt <<EOF
[binaries]
c = '$PHAZEOS/toolchain/bin/$target-gcc'
cpp = '$PHAZEOS/toolchain/bin/$target-g++'
ar = '$PHAZEOS/toolchain/bin/$target-ar'
strip = '$PHAZEOS/toolchain/bin/$target-strip'
pkgconfig = '$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config'

[host_machine]
system = 'linux'
cpu_family = 'x86_64'
cpu = 'x86_64'
endian = 'little'

[built-in options]
c_args = ['-I$PHAZEOS/usr/include', '-I$PHAZEOS/usr/include/libxml2']
cpp_args = ['-I$PHAZEOS/usr/include', '-I$PHAZEOS/usr/include/libxml2']
c_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
cpp_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
EOF

# Use host meson (assuming it's installed on Jack's machine)
if ! command -v meson &> /dev/null; then
    echo "⚠️ Meson not found! Installing via pip..."
    pip3 install meson ninja --user --break-system-packages
    export PATH=$HOME/.local/bin:$PATH
fi

meson setup build --prefix=/usr --libdir=lib --cross-file cross_file.txt -Ddocumentation=false -Dtests=false
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 5. Wayland Protocols
echo "🔨 Building Wayland Protocols..."
cd $BUILD
rm -rf wayland-protocols-$WAYLAND_PROTOCOLS_VER
tar -xf $SOURCES/wayland-protocols-$WAYLAND_PROTOCOLS_VER.tar.xz
cd wayland-protocols-$WAYLAND_PROTOCOLS_VER
meson setup build --prefix=/usr --cross-file ../wayland-$WAYLAND_VER/cross_file.txt -Dtests=false
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

echo "✅ Graphics Foundation Built!"
echo "Rebuilding VDI..."
cd $PHAZEOS
./16-build-vdi-disk.sh
