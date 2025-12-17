#!/bin/bash
# PhazeOS From Scratch - Toolchain Build
# Builds the cross-compilation toolchain

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
TOOLCHAIN=$PHAZEOS/toolchain
BUILD=$PHAZEOS/build
LOGS=$PHAZEOS/build-logs

mkdir -p $TOOLCHAIN $BUILD $LOGS

# CPU cores for parallel compilation
MAKEFLAGS="-j$(nproc)"

# ============================================
# SMART HELPER FUNCTIONS
# ============================================

# Safe directory creation - creates if doesn't exist, cleans if it does
safe_mkdir() {
    local dir=$1
    if [ -d "$dir" ]; then
        rm -rf "$dir"
    fi
    mkdir -p "$dir"
}

# Safe build directory - ensures clean build
safe_build_dir() {
    local build_dir="build"
    if [ -d "$build_dir" ]; then
        echo "Cleaning existing build directory..."
        rm -rf "$build_dir"
    fi
    mkdir -p "$build_dir"
    cd "$build_dir"
}

# Safe symlink creation - won't fail if target doesn't exist
safe_ln() {
    local target=$1
    local link=$2
    # Remove existing symlink if it exists
    [ -L "$link" ] && rm -f "$link"
    # Remove existing file if it exists
    [ -f "$link" ] && rm -f "$link"
    # Create symlink, ignore errors
    ln -sfv "$target" "$link" 2>/dev/null || true
}

# Check command success
check_success() {
    if [ $? -ne 0 ]; then
        echo "❌ Error: $1"
        echo "Check logs in $LOGS"
        exit 1
    fi
}

echo "=========================================="
echo "  BUILDING PHAZEOS TOOLCHAIN"
echo "=========================================="
echo ""
echo "This will take 1-3 hours depending on your system."
echo "Build logs will be saved to: $LOGS"
echo ""

cd $BUILD

# ============================================
# STEP 1: BINUTILS PASS 1
# ============================================
echo "🔨 [1/7] Building Binutils (Pass 1)..."
tar -xf $SOURCES/binutils-2.42.tar.xz || check_success "Failed to extract binutils"
cd binutils-2.42
safe_build_dir

../configure \
    --prefix=$TOOLCHAIN \
    --with-sysroot=$PHAZEOS \
    --target=x86_64-phazeos-linux-gnu \
    --disable-nls \
    --enable-gprofng=no \
    --disable-werror \
    --enable-default-hash-style=gnu 2>&1 | tee $LOGS/01-binutils-pass1-configure.log

make $MAKEFLAGS 2>&1 | tee $LOGS/01-binutils-pass1-make.log
make install 2>&1 | tee $LOGS/01-binutils-pass1-install.log

cd $BUILD
rm -rf binutils-2.42
echo "✅ Binutils Pass 1 complete!"
echo ""

# ============================================
# STEP 2: LINUX HEADERS
# ============================================
echo "🔨 [2/7] Installing Linux API Headers..."
tar -xf $SOURCES/linux-6.7.4.tar.xz
cd linux-6.7.4

make mrproper 2>&1 | tee $LOGS/02-linux-headers-mrproper.log
make headers 2>&1 | tee $LOGS/02-linux-headers-make.log
find usr/include -type f ! -name '*.h' -delete
cp -rv usr/include $TOOLCHAIN/

cd $BUILD
rm -rf linux-6.7.4
echo "✅ Linux headers installed!"
echo ""

# ============================================
# STEP 3: GCC PASS 1 (minimal)
# ============================================
echo "🔨 [3/7] Building GCC (Pass 1 - minimal)..."
tar -xf $SOURCES/gcc-13.2.0.tar.xz || check_success "Failed to extract GCC"
cd gcc-13.2.0

# Download prerequisites
contrib/download_prerequisites || check_success "Failed to download GCC prerequisites"

safe_build_dir

../configure \
    --target=x86_64-phazeos-linux-gnu \
    --prefix=$TOOLCHAIN \
    --with-glibc-version=2.39 \
    --with-sysroot=$PHAZEOS \
    --with-newlib \
    --without-headers \
    --enable-default-pie \
    --enable-default-ssp \
    --disable-nls \
    --disable-shared \
    --disable-multilib \
    --disable-threads \
    --disable-libatomic \
    --disable-libgomp \
    --disable-libquadmath \
    --disable-libssp \
    --disable-libvtv \
    --disable-libstdcxx \
    --enable-languages=c,c++ 2>&1 | tee $LOGS/03-gcc-pass1-configure.log

make $MAKEFLAGS 2>&1 | tee $LOGS/03-gcc-pass1-make.log
make install 2>&1 | tee $LOGS/03-gcc-pass1-install.log

cd $BUILD
rm -rf gcc-13.2.0
echo "✅ GCC Pass 1 complete!"
echo ""

# ============================================
# STEP 4: GLIBC
# ============================================
echo "🔨 [4/7] Building Glibc..."
tar -xf $SOURCES/glibc-2.39.tar.xz || check_success "Failed to extract Glibc"
cd glibc-2.39

safe_build_dir

# Create dynamic linker symlinks (safe version)
mkdir -p $TOOLCHAIN/lib || true
safe_ln ../lib/ld-linux-x86-64.so.2 $TOOLCHAIN/lib64
safe_ln ../lib/ld-linux-x86-64.so.2 $TOOLCHAIN/lib64/ld-lsb-x86-64.so.3

../configure \
    --prefix=/usr \
    --host=x86_64-phazeos-linux-gnu \
    --build=$(../scripts/config.guess) \
    --enable-kernel=4.19 \
    --with-headers=$TOOLCHAIN/include \
    --disable-nscd \
    libc_cv_slibdir=/usr/lib 2>&1 | tee $LOGS/04-glibc-configure.log

make $MAKEFLAGS 2>&1 | tee $LOGS/04-glibc-make.log
make DESTDIR=$PHAZEOS install 2>&1 | tee $LOGS/04-glibc-install.log

# Fix
sed '/RTLDLIST=/s@/usr@@g' -i $PHAZEOS/usr/bin/ldd

cd $BUILD
rm -rf glibc-2.39
echo "✅ Glibc complete!"
echo ""

# ============================================
# STEP 5: GCC PASS 2 (full)
# ============================================
echo "🔨 [5/7] Building GCC (Pass 2 - full compiler)..."
tar -xf $SOURCES/gcc-13.2.0.tar.xz || check_success "Failed to extract GCC Pass 2"
cd gcc-13.2.0

safe_build_dir

../configure \
    --target=x86_64-phazeos-linux-gnu \
    --prefix=$TOOLCHAIN \
    --with-sysroot=$PHAZEOS \
    --enable-default-pie \
    --enable-default-ssp \
    --disable-nls \
    --disable-multilib \
    --enable-languages=c,c++ 2>&1 | tee $LOGS/05-gcc-pass2-configure.log

make $MAKEFLAGS 2>&1 | tee $LOGS/05-gcc-pass2-make.log
make install 2>&1 | tee $LOGS/05-gcc-pass2-install.log

cd $BUILD
rm -rf gcc-13.2.0
echo "✅ GCC Pass 2 complete!"
echo ""

# ============================================
# STEP 6: BINUTILS PASS 2
# ============================================
echo "🔨 [6/7] Building Binutils (Pass 2 - final)..."
tar -xf $SOURCES/binutils-2.42.tar.xz || check_success "Failed to extract Binutils Pass 2"
cd binutils-2.42

safe_build_dir

../configure \
    --prefix=/usr \
    --host=x86_64-phazeos-linux-gnu \
    --build=$(../config.guess) \
    --disable-nls \
    --enable-shared \
    --enable-gprofng=no \
    --disable-werror \
    --enable-64-bit-bfd \
    --enable-default-hash-style=gnu 2>&1 | tee $LOGS/06-binutils-pass2-configure.log

make $MAKEFLAGS 2>&1 | tee $LOGS/06-binutils-pass2-make.log
make DESTDIR=$PHAZEOS install 2>&1 | tee $LOGS/06-binutils-pass2-install.log

cd $BUILD
rm -rf binutils-2.42
echo "✅ Binutils Pass 2 complete!"
echo ""

# ============================================
# STEP 7: VERIFICATION
# ============================================
echo "🔨 [7/7] Verifying toolchain..."

# Test compiler
echo 'int main(){}' | $TOOLCHAIN/bin/x86_64-phazeos-linux-gnu-gcc -x c -
if [ -f a.out ]; then
    echo "✅ Cross-compiler works!"
    rm a.out
else
    echo "❌ Cross-compiler test failed!"
    exit 1
fi

# Save toolchain info
cat > $TOOLCHAIN/toolchain-info.txt << EOF
PhazeOS Toolchain Build Information
====================================
Build Date: $(date)
Host System: $(uname -a)
GCC Version: $($TOOLCHAIN/bin/x86_64-phazeos-linux-gnu-gcc --version | head -n1)
Binutils Version: $($TOOLCHAIN/bin/x86_64-phazeos-linux-gnu-ld --version | head -n1)

Directory Structure:
- Toolchain: $TOOLCHAIN
- System Root: $PHAZEOS
- Sources: $SOURCES
- Build Logs: $LOGS

Build completed successfully!
EOF

echo ""
echo "=========================================="
echo "✅ TOOLCHAIN BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Toolchain installed to: $TOOLCHAIN"
echo "Build logs saved to: $LOGS"
echo ""
echo "Next step: ./03-build-base-system.sh"
echo ""
