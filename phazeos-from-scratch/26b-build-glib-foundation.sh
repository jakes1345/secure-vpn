#!/bin/bash
# PhazeOS - Phase 3b: GLib Foundation (Critical for Desktop)
# Builds Zlib, PCRE2, Util-Linux (Libs), GLib

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

# Versions
ZLIB_VER="1.3.1"
PCRE2_VER="10.42"
UTIL_LINUX_VER="2.39.3"
GLIB_VER="2.80.0"

echo "=========================================="
echo "  PHASE 3b: GLIB FOUNDATION"
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
download "https://zlib.net/zlib-$ZLIB_VER.tar.gz"
download "https://github.com/PCRE2Project/pcre2/releases/download/pcre2-$PCRE2_VER/pcre2-$PCRE2_VER.tar.bz2"
download "https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/v${UTIL_LINUX_VER%.*}/util-linux-$UTIL_LINUX_VER.tar.xz"
download "https://download.gnome.org/sources/glib/${GLIB_VER%.*}/glib-$GLIB_VER.tar.xz"

# Create Cross File for Meson if not exists
if [ ! -f "$BUILD/cross_file.txt" ]; then
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
c_args = ['-I$PHAZEOS/usr/include']
cpp_args = ['-I$PHAZEOS/usr/include']
c_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
cpp_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
EOF
fi

# 1. Zlib
echo "🔨 Building Zlib..."
cd $BUILD
rm -rf zlib-$ZLIB_VER
tar -xf $SOURCES/zlib-$ZLIB_VER.tar.gz
cd zlib-$ZLIB_VER
CC=$TARGET-gcc ./configure --prefix=/usr
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 2. PCRE2
echo "🔨 Building PCRE2..."
cd $BUILD
rm -rf pcre2-$PCRE2_VER
tar -xf $SOURCES/pcre2-$PCRE2_VER.tar.bz2
cd pcre2-$PCRE2_VER
./configure --host=$TARGET --prefix=/usr --enable-jit --disable-static
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 3. Util-Linux (Libs only: uuid, blkid, mount)
echo "🔨 Building Util-Linux (Libs)..."
cd $BUILD
rm -rf util-linux-$UTIL_LINUX_VER
tar -xf $SOURCES/util-linux-$UTIL_LINUX_VER.tar.xz
cd util-linux-$UTIL_LINUX_VER
./configure --host=$TARGET --prefix=/usr \
    --disable-all-programs \
    --enable-libuuid --enable-libblkid --enable-libmount \
    --disable-static
make -j$(nproc)
make DESTDIR=$PHAZEOS install



# Pre-requisites: Gettext and Libiconv (for solid foundation)
GETTEXT_VER="0.22.4"
LIBICONV_VER="1.17"

echo "📦 Downloading Extra Build Deps..."
download "https://ftp.gnu.org/pub/gnu/gettext/gettext-$GETTEXT_VER.tar.gz"
download "https://ftp.gnu.org/pub/gnu/libiconv/libiconv-$LIBICONV_VER.tar.gz"

# 0a. Libiconv
echo "🔨 Building Libiconv..."
cd $BUILD
rm -rf libiconv-$LIBICONV_VER
tar -xf $SOURCES/libiconv-$LIBICONV_VER.tar.gz
cd libiconv-$LIBICONV_VER
./configure --host=$TARGET --prefix=/usr --disable-static
make -j$(nproc)
make DESTDIR=$PHAZEOS install


# 0b. Gettext (Libintl) - Runtime only (sufficient for GLib)
echo "🔨 Building Gettext (Runtime)..."
cd $BUILD
rm -rf gettext-$GETTEXT_VER
tar -xf $SOURCES/gettext-$GETTEXT_VER.tar.gz
cd gettext-$GETTEXT_VER/gettext-runtime
./configure --host=$TARGET --prefix=/usr --disable-static --disable-java --disable-csharp
make -j$(nproc)
make DESTDIR=$PHAZEOS install

# 4. GLib
echo "🔨 Building GLib..."
cd $BUILD
rm -rf glib-$GLIB_VER
tar -xf $SOURCES/glib-$GLIB_VER.tar.xz

cd glib-$GLIB_VER
# Patch _POSIX_HOST_NAME_MAX issue
sed -i 's/_POSIX_HOST_NAME_MAX/255/g' glib/ghostutils.c

# GLib is picky. Using meson.
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" \
    -Dtests=false \
    -Dman-pages=disabled \
    -Dselinux=disabled \
    -Dlibmount=enabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

echo "✅ GLib Foundation Built!"
