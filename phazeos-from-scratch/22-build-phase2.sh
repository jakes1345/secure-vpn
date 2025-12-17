#!/bin/bash
# PhazeOS - Phase 2 Build
# Compiles Networking, Security, and Editors

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
LOGS=$PHAZEOS/build-logs
target="x86_64-phazeos-linux-gnu"

export PATH=$PHAZEOS/toolchain/bin:$PATH
export CC=$target-gcc
export CXX=$target-g++
export AR=$target-ar
export AS=$target-as
export RANLIB=$target-ranlib
export LD=$target-ld
export STRIP=$target-strip

echo "=========================================="
echo "  BUILDING PHASE 2 PACKAGES"
echo "=========================================="

mkdir -p $BUILD $LOGS
cd $BUILD

# Helper function
build_package() {
    local NAME=$1
    local TARBALL=$2
    local DIRNAME=$3
    local BUILD_CMD=$4
    local INSTALL_CMD=$5
    
    echo "🔨 Building $NAME..."
    
    if [ ! -f "$SOURCES/$TARBALL" ]; then
        echo "❌ Source $TARBALL not found!"
        exit 1
    fi

    rm -rf $DIRNAME
    tar -xf $SOURCES/$TARBALL
    cd $DIRNAME
    
    eval $BUILD_CMD 2>&1 | tee $LOGS/phase2-$NAME-build.log
    if [ $? -ne 0 ]; then
        echo "❌ Build failed for $NAME"
        exit 1
    fi
    
    eval $INSTALL_CMD 2>&1 | tee $LOGS/phase2-$NAME-install.log
    
    cd $BUILD
    rm -rf $DIRNAME
    echo "✅ $NAME complete!"
    echo ""
}

# 1. Zlib (Dependency)
build_package "zlib" "zlib-1.3.1.tar.gz" "zlib-1.3.1" \
    "CC=$target-gcc ./configure --prefix=/usr --shared" \
    "make && make DESTDIR=$PHAZEOS install"

# 2. OpenSSL
# OpenSSL doesn't use standard autoconf
echo "🔨 Building OpenSSL..."
rm -rf openssl-3.2.1
tar -xf $SOURCES/openssl-3.2.1.tar.gz
cd openssl-3.2.1

./Configure linux-x86_64 \
    --prefix=/usr \
    --openssldir=/etc/ssl \
    --libdir=lib \
    shared zlib-dynamic \
    --cross-compile-prefix=$target- \
    2>&1 | tee $LOGS/phase2-openssl-config.log

make -j$(nproc) 2>&1 | tee $LOGS/phase2-openssl-make.log
make DESTDIR=$PHAZEOS install_sw 2>&1 | tee $LOGS/phase2-openssl-install.log

cd $BUILD
rm -rf openssl-3.2.1
echo "✅ OpenSSL complete!"
echo ""

# 3. Procps-ng (ps, top)
build_package "procps-ng" "procps-ng-4.0.4.tar.xz" "procps-ng-4.0.4" \
    "./configure --prefix=/usr --host=$target --disable-kill --without-systemd" \
    "make -j$(nproc) && make DESTDIR=$PHAZEOS install"

# 4. Nano
build_package "nano" "nano-7.2.tar.xz" "nano-7.2" \
    "./configure --prefix=/usr --host=$target --enable-utf8" \
    "make -j$(nproc) && make DESTDIR=$PHAZEOS install"

# 5. DHCPCD
build_package "dhcpcd" "dhcpcd-10.0.6.tar.xz" "dhcpcd-10.0.6" \
    "./configure --prefix=/usr --sysconfdir=/etc --host=$target --dbdir=/var/lib/dhcpcd" \
    "make -j$(nproc) && make DESTDIR=$PHAZEOS install"

# 6. IPRoute2
# This one is tricky, needs manual Makefile tweaks or env vars
echo "🔨 Building IPRoute2..."
rm -rf iproute2-6.7.0
tar -xf $SOURCES/iproute2-6.7.0.tar.xz
cd iproute2-6.7.0

# It uses PKG_CONFIG to find libs, we might need to point it or disable things
# For now, minimal build
make CC=$CC AR=$AR KERNEL_INCLUDE=$PHAZEOS/usr/include \
     SUBDIRS="lib ip" \
     -j$(nproc) 2>&1 | tee $LOGS/phase2-iproute2-make.log

# We only want 'ip' mostly
make DESTDIR=$PHAZEOS SUBDIRS="lib ip" install 2>&1 | tee $LOGS/phase2-iproute2-install.log

cd $BUILD
rm -rf iproute2-6.7.0
echo "✅ IPRoute2 complete!"

echo ""
echo "=========================================="
echo "🎉 PHASE 2 BUILD COMPLETE!"
echo "=========================================="
echo "Rebuilding disk image..."
$PHAZEOS/16-build-vdi-disk.sh
