#!/bin/bash
# PhazeOS - Phase 3c: Rendering Stack (Cairo/Pango)
# Essential for Text and UI elements in Labwc

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
TARGET="x86_64-phazeos-linux-gnu"
export PATH=$PHAZEOS/toolchain/bin:$HOME/.local/bin:$PATH
export CC="$TARGET-gcc"
export CXX="$TARGET-g++"
export AR="$TARGET-ar"
export RANLIB="$TARGET-ranlib"
export PKG_CONFIG="$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config"

FRIBIDI_VER="1.0.13"
CAIRO_VER="1.18.0"
PANGO_VER="1.52.0"

echo "=========================================="
echo "  PHASE 3c: RENDERING STACK"
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

echo "📦 Downloading..."
download "https://github.com/fribidi/fribidi/releases/download/v$FRIBIDI_VER/fribidi-$FRIBIDI_VER.tar.xz"
download "https://cairographics.org/releases/cairo-$CAIRO_VER.tar.xz"
download "https://download.gnome.org/sources/pango/${PANGO_VER%.*}/pango-$PANGO_VER.tar.xz"


# Create Cross File for Meson if not exists (Ensure pkg-config is correct)
cat > "$BUILD/cross_file.txt" <<EOF
[binaries]
c = '$TARGET-gcc'
cpp = '$TARGET-g++'
ar = '$TARGET-ar'
strip = '$TARGET-strip'
pkg-config = '$PKG_CONFIG'

[host_machine]
system = 'linux'
cpu_family = 'x86_64'
cpu = 'x86_64'
endian = 'little'

[built-in options]
c_args = ['-I$PHAZEOS/usr/include', '-I$PHAZEOS/usr/include/libxml2']
cpp_args = ['-I$PHAZEOS/usr/include', '-I$PHAZEOS/usr/include/libxml2', '-I$PHAZEOS/toolchain/$TARGET/include/c++', '-I$PHAZEOS/toolchain/$TARGET/include/c++/x86_64-linux-gnu']
c_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
cpp_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
EOF

# 1. FriBidi (Bi-directional text)
echo "🔨 Building FriBidi..."
cd $BUILD
rm -rf fribidi-$FRIBIDI_VER
tar -xf $SOURCES/fribidi-$FRIBIDI_VER.tar.xz
cd fribidi-$FRIBIDI_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Ddocs=false -Dtests=false
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 2. Cairo (2D Graphics)
echo "🔨 Building Cairo..."
cd $BUILD
rm -rf cairo-$CAIRO_VER
tar -xf $SOURCES/cairo-$CAIRO_VER.tar.xz
cd cairo-$CAIRO_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" \
    -Dtests=disabled -Dxcb=disabled -Dxlib=disabled -Dzlib=enabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 3. Pango (Text Layout)
echo "🔨 Building Pango..."
cd $BUILD
rm -rf pango-$PANGO_VER
tar -xf $SOURCES/pango-$PANGO_VER.tar.xz
cd pango-$PANGO_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" \
    -Dgtk_doc=false \
    -Dintrospection=disabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

echo "✅ Rendering Stack Built!"
