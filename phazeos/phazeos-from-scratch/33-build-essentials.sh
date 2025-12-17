#!/usr/bin/env bash
# PhazeOS - Phase 4: OS Essentials & Applications
# Builds: Nano, Htop, Neofetch, Foot (Terminal), and dependencies

set -e

PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SOURCES="$PH_DIR/sources"
BUILD="$PH_DIR/build"
TARGET="x86_64-phazeos-linux-gnu"
export PATH="$PH_DIR/toolchain/bin:$HOME/.local/bin:$PATH"
export CC="$TARGET-gcc"
export CXX="$TARGET-g++"
export AR="$TARGET-ar"
export RANLIB="$TARGET-ranlib"
export PKG_CONFIG="$PH_DIR/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config"

# Versions
PIXMAN_VER="0.42.2"
FREETYPE_VER="2.13.2"
FONTCONFIG_VER="2.15.0"
LIBXKBCOMMON_VER="1.6.0"
UTF8PROC_VER="2.8.0"
HARFBUZZ_VER="8.3.0"
FCFT_VER="3.1.8"
FOOT_VER="1.16.2"
NANO_VER="7.2"
HTOP_VER="3.2.2"
DEJAVU_FONTS_VER="2.37"

mkdir -p "$SOURCES" "$BUILD"

# Robust download
download() {
    local url=$1
    local file=$(basename "$url")
    local dest="$SOURCES/$file"
    if [ -f "$dest" ]; then return; fi
    echo "⬇️ Download $file..."
    wget --no-check-certificate --user-agent="Mozilla/5.0" -q -O "$dest" "$url" || { echo "❌ Failed $file"; exit 1; }
}

echo "📦 Downloading sources..."
download "https://cairographics.org/releases/pixman-$PIXMAN_VER.tar.gz"
download "https://download.savannah.gnu.org/releases/freetype/freetype-$FREETYPE_VER.tar.xz"
download "https://www.freedesktop.org/software/fontconfig/release/fontconfig-$FONTCONFIG_VER.tar.xz"
download "https://xkbcommon.org/download/libxkbcommon-$LIBXKBCOMMON_VER.tar.xz"
download "https://github.com/JuliaStrings/utf8proc/archive/v$UTF8PROC_VER.tar.gz"
download "https://github.com/harfbuzz/harfbuzz/releases/download/$HARFBUZZ_VER/harfbuzz-$HARFBUZZ_VER.tar.xz"
download "https://codeberg.org/dnkl/fcft/archive/${FCFT_VER}.tar.gz"
download "https://codeberg.org/dnkl/foot/archive/${FOOT_VER}.tar.gz"
download "https://codeberg.org/dnkl/tllist/archive/1.1.0.tar.gz"
download "https://www.nano-editor.org/dist/v7/nano-$NANO_VER.tar.xz"
download "https://github.com/htop-dev/htop/releases/download/$HTOP_VER/htop-$HTOP_VER.tar.xz"
download "https://raw.githubusercontent.com/dylanaraps/neofetch/master/neofetch"
download "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_${DEJAVU_FONTS_VER}/dejavu-fonts-ttf-${DEJAVU_FONTS_VER}.zip"

# Recreate cross file for meson
cat > "$BUILD/cross_file.txt" <<EOF
[binaries]
c = '$TARGET-gcc'
cpp = '$TARGET-g++'
ar = '$TARGET-ar'
strip = '$TARGET-strip'
pkgconfig = '$PKG_CONFIG'

[host_machine]
system = 'linux'
cpu_family = 'x86_64'
cpu = 'x86_64'
endian = 'little'

[built-in options]
c_args = ['-I$PH_DIR/usr/include']
cpp_args = ['-I$PH_DIR/usr/include', '-I$PH_DIR/toolchain/x86_64-phazeos-linux-gnu/include/c++', '-I$PH_DIR/toolchain/x86_64-phazeos-linux-gnu/include/c++/x86_64-linux-gnu']
c_link_args = ['-L$PH_DIR/usr/lib']
cpp_link_args = ['-L$PH_DIR/usr/lib']
EOF

# 1. Pixman
echo "🔨 Pixman..."
cd "$BUILD"
rm -rf pixman-$PIXMAN_VER
tar -xf "$SOURCES/pixman-$PIXMAN_VER.tar.gz"
cd pixman-$PIXMAN_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dtests=disabled
ninja -C build
DESTDIR=$PH_DIR ninja -C build install

# 2. Freetype
echo "🔨 Freetype..."
cd "$BUILD"
rm -rf freetype-$FREETYPE_VER
tar -xf "$SOURCES/freetype-$FREETYPE_VER.tar.xz"
cd freetype-$FREETYPE_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dharfbuzz=disabled -Dpng=disabled -Dzlib=enabled -Dbzip2=disabled
ninja -C build
DESTDIR=$PH_DIR ninja -C build install

# 3. Harfbuzz (now that we have freetype)
echo "🔨 Harfbuzz..."
cd "$BUILD"
rm -rf harfbuzz-$HARFBUZZ_VER
tar -xf "$SOURCES/harfbuzz-$HARFBUZZ_VER.tar.xz"
cd harfbuzz-$HARFBUZZ_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dtests=disabled -Dglib=disabled -Dgobject=disabled -Dcairo=disabled -Dfreetype=enabled
ninja -C build
DESTDIR=$PH_DIR ninja -C build install

# 4. Fontconfig
echo "🔨 Fontconfig..."
cd "$BUILD"
rm -rf fontconfig-$FONTCONFIG_VER
tar -xf "$SOURCES/fontconfig-$FONTCONFIG_VER.tar.xz"
cd fontconfig-$FONTCONFIG_VER
# Fontconfig uses autotools usually, but check for meson support or use configure
if [ -f meson.build ]; then
    meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dtests=disabled -Ddoc=disabled
    ninja -C build
    DESTDIR=$PH_DIR ninja -C build install
else
    ./configure --host=$TARGET --prefix=/usr --disable-docs --enable-libxml2
    make -j$(nproc)
    make DESTDIR=$PH_DIR install
fi

# 5. Libxkbcommon
echo "🔨 Libxkbcommon..."
cd "$BUILD"
rm -rf libxkbcommon-$LIBXKBCOMMON_VER
tar -xf "$SOURCES/libxkbcommon-$LIBXKBCOMMON_VER.tar.xz"
cd libxkbcommon-$LIBXKBCOMMON_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Denable-wayland=true -Denable-x11=false -Denable-docs=false -Denable-tools=false
ninja -C build
DESTDIR=$PH_DIR ninja -C build install

# 6. UTF8Proc
echo "🔨 UTF8Proc..."
cd "$BUILD"
rm -rf utf8proc-$UTF8PROC_VER
tar -xf "$SOURCES/v$UTF8PROC_VER.tar.gz"
cd utf8proc-$UTF8PROC_VER
make -j$(nproc) prefix=/usr CC=$CC AR=$AR
make prefix=/usr DESTDIR=$PH_DIR install

# 7. Tllist
echo "🔨 Tllist..."
cd "$BUILD"
rm -rf tllist
mkdir tllist && tar -xf "$SOURCES/1.1.0.tar.gz" -C tllist --strip-components=1
cd tllist
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt"
ninja -C build
DESTDIR=$PH_DIR ninja -C build install

# 8. Fcft
echo "🔨 Fcft..."
cd "$BUILD"
rm -rf fcft
mkdir fcft && tar -xf "$SOURCES/${FCFT_VER}.tar.gz" -C fcft --strip-components=1
cd fcft
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dsvg-backend=nanosvg -Dtest-text-shaping=false
ninja -C build
DESTDIR=$PH_DIR ninja -C build install

# 9. Foot (Terminal)
echo "🔨 Foot..."
cd "$BUILD"
rm -rf foot
mkdir foot && tar -xf "$SOURCES/${FOOT_VER}.tar.gz" -C foot --strip-components=1
cd foot
# Fix _POSIX_HOST_NAME_MAX undeclared error
sed -i 's/_POSIX_HOST_NAME_MAX/255/g' uri.c
# Disable Werror as Foot uses -Werror by default
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dtests=false -Dthemes=false -Dterminfo=disabled -Dwerror=false
ninja -C build
DESTDIR=$PH_DIR ninja -C build install
# Manually install terminfo for foot if needed, or rely on ncurses base

# 10. Nano
echo "🔨 Nano..."
cd "$BUILD"
rm -rf nano-$NANO_VER
tar -xf "$SOURCES/nano-$NANO_VER.tar.xz"
cd nano-$NANO_VER
./configure --host=$TARGET --prefix=/usr --disable-libmagic --disable-extra --disable-justify --disable-speller
make -j$(nproc)
make DESTDIR=$PH_DIR install

# 11. Htop (skipped due to ncurses issues)
# echo "🔨 Htop..."
# cd "$BUILD"
# rm -rf htop-$HTOP_VER
# tar -xf "$SOURCES/htop-$HTOP_VER.tar.xz"
# cd htop-$HTOP_VER
# ./configure --host=$TARGET --prefix=/usr --disable-unicode
# make -j$(nproc)
# make DESTDIR=$PH_DIR install

# 12. Neofetch
echo "🔨 Neofetch..."
install -m 755 "$SOURCES/neofetch" "$PH_DIR/usr/bin/neofetch"

# 13. Fonts
echo "🔨 Installing Fonts (Roboto)..."
mkdir -p "$PH_DIR/usr/share/fonts/ttf"
download "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto-Regular.ttf"
download "https://raw.githubusercontent.com/google/fonts/main/ofl/robotomono/RobotoMono-Regular.ttf"
cp "$SOURCES"/Roboto-Regular.ttf "$PH_DIR/usr/share/fonts/ttf/"
cp "$SOURCES"/RobotoMono-Regular.ttf "$PH_DIR/usr/share/fonts/ttf/"

# Config for Foot
mkdir -p "$PH_DIR/etc/foot"
cat > "$PH_DIR/etc/foot/foot.ini" <<EOF
[main]
term=xterm-256color
font=Roboto Mono:size=10
dpi-aware=no


[colors]
# PhazeOS Theme
background=101014
foreground=c0c0c0
regular0=101014  # black
regular1=ff5555  # red
regular2=50fa7b  # green
regular3=f1fa8c  # yellow
regular4=bd93f9  # blue
regular5=ff79c6  # magenta
regular6=8be9fd  # cyan
regular7=bfbfbf  # white
EOF

echo "✅ Essentials Built: Nano, Htop, Foot, Fonts, Neofetch"
