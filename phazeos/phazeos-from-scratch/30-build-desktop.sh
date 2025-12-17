#!/usr/bin/env bash
# PhazeOS - Desktop component build (robust version)
# Builds labwc, waybar, wofi, mako, swaybg and installs them into the sysroot.

set -e

# ---------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------
PHAZEOS="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SOURCES="$PHAZEOS/sources"
BUILD="$PHAZEOS/build"
TARGET="x86_64-phazeos-linux-gnu"
export PATH="$PHAZEOS/toolchain/bin:$HOME/.local/bin:$PATH"
export CC="$TARGET-gcc"
export CXX="$TARGET-g++"
export AR="$TARGET-ar"
export RANLIB="$TARGET-ranlib"
export PKG_CONFIG_PATH="$PHAZEOS/usr/lib/pkgconfig:$PHAZEOS/usr/share/pkgconfig"
export PKG_CONFIG="$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-pkg-config"

# ---------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------
LABWC_VER="0.7.1"
WAYBAR_VER="0.9.24"
WOFI_VER="v1.4.1" # Using v prefix if tag requires it, but usually standard tarballs don't
MAKO_VER="1.8.0"
SWAYBG_VER="1.2.0"
WLROOTS_VER="0.17.1" # Labwc needs wlroots

mkdir -p "$SOURCES" "$BUILD"

download() {
    local url="$1"
    local file=$(basename "$url")
    local dest="$SOURCES/$file"
    if [ -f "$dest" ]; then return; fi
    echo "⬇️ Downloading $file..."
    wget --no-check-certificate --user-agent="Mozilla/5.0" -q -O "$dest" "$url" || {
        echo "❌ wget failed for $file" >&2; exit 1;
    }
}


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
c_args = ['-I$PHAZEOS/usr/include', '-I$PHAZEOS/usr/include/libxml2', '-I$PHAZEOS/usr/include/pixman-1']
cpp_args = ['-I$PHAZEOS/usr/include', '-I$PHAZEOS/usr/include/libxml2']
c_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
cpp_link_args = ['-L$PHAZEOS/usr/lib', '-L$PHAZEOS/lib']
EOF
fi

echo "📦 Downloading Desktop Sources..."
# Labwc
download "https://github.com/labwc/labwc/archive/refs/tags/${LABWC_VER}.tar.gz"

# Waybar
download "https://github.com/Alexays/Waybar/archive/refs/tags/${WAYBAR_VER}.tar.gz"

# Wofi (Git Clone used in build step)

# Mako
download "https://github.com/emersion/mako/archive/refs/tags/v${MAKO_VER}.tar.gz"

# Swaybg
download "https://github.com/swaywm/swaybg/archive/refs/tags/v${SWAYBG_VER}.tar.gz"

# WLROOTS
download "https://gitlab.freedesktop.org/wlroots/wlroots/-/archive/${WLROOTS_VER}/wlroots-${WLROOTS_VER}.tar.gz"

# 0. WLROOTS (Critical Dependency)
echo "🔨 Building Wlroots..."
cd "$BUILD"
rm -rf wlroots-$WLROOTS_VER
tar -xf "$SOURCES/wlroots-$WLROOTS_VER.tar.gz"
cd wlroots-$WLROOTS_VER
# Fix syntax for array options: use comma separated, no brackets for cli? 
# or just rely on defaults which are sensible (auto).
# Using -Drenderers=gles2 -Dbackends=drm,libinput
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dexamples=false -Drenderers=gles2 -Dbackends=drm,libinput
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 1. Labwc (Window Manager)
echo "🔨 Building Labwc..."
cd "$BUILD"
rm -rf labwc labwc-$LABWC_VER
tar -xf "$SOURCES/$LABWC_VER.tar.gz"
mv labwc-$LABWC_VER labwc # rename for easier cd
cd labwc
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dman-pages=disabled -Dxwayland=disabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install


# 2. Waybar (Panel) - SKIPPED: Requires GTK3 (too heavy for alpha)
# echo "🔨 Building Waybar..."
# cd "$BUILD"
# rm -rf Waybar-$WAYBAR_VER
# tar -xf "$SOURCES/$WAYBAR_VER.tar.gz"
# cd Waybar-$WAYBAR_VER
# meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" \
#     -Dman-pages=disabled
# ninja -C build
# DESTDIR=$PHAZEOS ninja -C build install




# 3. Wofi (Launcher)
echo "🔨 Building Wofi..."
cd "$BUILD"
rm -rf wofi
git clone https://github.com/SimplyCEO/wofi.git
cd wofi
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt"
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install


# 4. Mako (Notifications) - SKIPPED: Requires systemd/elogind/basu
# echo "🔨 Building Mako..."
# cd "$BUILD"
# rm -rf mako-$MAKO_VER
# tar -xf "$SOURCES/v${MAKO_VER}.tar.gz"
# cd mako-$MAKO_VER
# meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dman-pages=disabled
# ninja -C build
# DESTDIR=$PHAZEOS ninja -C build install

# 5. Swaybg (Wallpaper)
echo "🔨 Building Swaybg..."
cd "$BUILD"
rm -rf swaybg-$SWAYBG_VER
tar -xf "$SOURCES/v${SWAYBG_VER}.tar.gz"
cd swaybg-$SWAYBG_VER
meson setup build --prefix=/usr --cross-file "$BUILD/cross_file.txt" -Dman-pages=disabled
ninja -C build
DESTDIR=$PHAZEOS ninja -C build install

# 6. Configuration (The "Ricering")
echo "🎨 Configuring Desktop Theme..."
mkdir -p "$PHAZEOS/etc/labwc"
mkdir -p "$PHAZEOS/etc/waybar"
mkdir -p "$PHAZEOS/usr/share/backgrounds"

# Labwc Autostart
cat > "$PHAZEOS/etc/labwc/autostart" <<EOF
swaybg -i /usr/share/backgrounds/phazeos_bg.png -m fill &
EOF
chmod +x "$PHAZEOS/etc/labwc/autostart"

# Labwc RC
cat > "$PHAZEOS/etc/labwc/rc.xml" <<EOF
<labwc_config>
  <windowRules>
    <windowRule identifier="*" serverDecoration="yes" />
  </windowRules>
  <theme>
    <name>PhazeDark</name>
    <font>Roboto 10</font>
  </theme>
</labwc_config>
EOF

# Waybar Config
cat > "$PHAZEOS/etc/waybar/config" <<EOF
{
    "layer": "top",
    "position": "top",
    "height": 30,
    "modules-left": ["custom/launcher", "wlr/taskbar"],
    "modules-center": ["clock"],
    "modules-right": ["network", "battery", "tray"],
    "custom/launcher": {
        "format": "🚀",
        "on-click": "wofi --show drun"
    },
    "clock": {
        "format": "{:%H:%M}  ",
        "tooltip-format": "<big>{:%Y %B}</big>\n<tt><small>{calendar}</small></tt>"
    },
    "network": {
        "format-wifi": "{essid} ({signalStrength}%) ",
        "format-ethernet": "{ipaddr}/{cidr} ",
        "tooltip-format": "{ifname} via {gwaddr} ",
        "format-linked": "{ifname} (No IP) ",
        "format-disconnected": "Disconnected ⚠",
        "format-alt": "{ifname}: {ipaddr}/{cidr}"
    }
}
EOF

# CSS for Waybar
cat > "$PHAZEOS/etc/waybar/style.css" <<EOF
* {
    border: none;
    border-radius: 0;
    font-family: Roboto Mono, monospace;
    font-size: 13px;
    min-height: 0;
}
window#waybar {
    background: rgba(20, 20, 30, 0.9);
    border-bottom: 2px solid rgba(100, 100, 200, 0.5);
    color: #ffffff;
}
#custom-launcher {
    background-color: #bd93f9;
    color: #282a36;
    padding: 0 10px;
}
#clock, #network, #battery, #tray {
    padding: 0 10px;
    margin: 0 4px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}
EOF


# 7. Install Firefox (Official Binary for Immediate GUI Capability)
echo "🌐 Installing Firefox..."
FIREFOX_URL="https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US"
if [ ! -d "$PHAZEOS/opt/firefox" ]; then
    echo "Downloading Firefox..."
    wget --no-check-certificate --user-agent="Mozilla/5.0" -q -O "$SOURCES/firefox-latest.tar.bz2" "$FIREFOX_URL"
    
    if [ -f "$SOURCES/firefox-latest.tar.bz2" ] && file "$SOURCES/firefox-latest.tar.bz2" | grep -q "bzip2"; then
        echo "Extracting Firefox..."
        mkdir -p "$PHAZEOS/opt"
        tar -xjf "$SOURCES/firefox-latest.tar.bz2" -C "$PHAZEOS/opt/"
    else
        echo "⚠️ Firefox download failed or invalid file. Skipping."
    fi
else
    echo "Firefox already installed in /opt."
fi

# Link binary if firefox exists
if [ -d "$PHAZEOS/opt/firefox" ]; then
    ln -sf /opt/firefox/firefox "$PHAZEOS/usr/bin/firefox"
    
    # Create Desktop Entry
    mkdir -p "$PHAZEOS/usr/share/applications"
    cat > "$PHAZEOS/usr/share/applications/firefox.desktop" <<EOF
[Desktop Entry]
Name=Firefox
Comment=Browse the World Wide Web
GenericName=Web Browser
Exec=firefox %u
Icon=/opt/firefox/browser/chrome/icons/default/default128.png
Type=Application
StartupNotify=true
Categories=Network;WebBrowser;
EOF
fi

# 8. Download a background
echo "🖼️ Downloading Background..."
download "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1920&auto=format&fit=crop"
mv "$SOURCES/photo-1451187580459-43490279c0fa?q=80&w=1920&auto=format&fit=crop" "$PHAZEOS/usr/share/backgrounds/phazeos_bg.png" || echo "Check background download"

echo "✅ Desktop Build Complete."
