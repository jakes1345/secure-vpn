#!/bin/bash
# PhazeOS - FINALIZE PHASE 1 (Static Edition)
# Uses built-in BusyBox features for a robust foundation

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
cd $PHAZEOS

echo "=========================================="
echo "  FINALIZING PHASE 1: STATIC FOUNDATION"
echo "=========================================="
echo ""

# 1. Networking (udhcpc)
# ----------------------------------------------------------------
echo "🌍 Configuring Networking (udhcpc)..."
mkdir -p usr/share/udhcpc

# Create the script udhcpc needs to configure the interface
cat > usr/share/udhcpc/default.script << 'EOF'
#!/bin/sh
# Simple udhcpc script

[ -z "$1" ] && echo "Error: should be called from udhcpc" && exit 1

case "$1" in
    deconfig)
        /sbin/ifconfig $interface 0.0.0.0
        ;;
    renew|bound)
        /sbin/ifconfig $interface $ip netmask $subnet
        if [ -n "$router" ]; then
            while route del default gw 0.0.0.0 dev $interface 2>/dev/null; do
                :
            done
            for i in $router; do
                route add default gw $i dev $interface
            done
        fi
        if [ -n "$dns" ]; then
            echo -n > /etc/resolv.conf
            for i in $dns; do
                echo "nameserver $i" >> /etc/resolv.conf
            done
        fi
        ;;
esac
exit 0
EOF
chmod +x usr/share/udhcpc/default.script

# Create a 'connect' alias for easy use
cat > usr/bin/connect << 'EOF'
#!/bin/sh
echo "Connecting to network..."
ifconfig eth0 up
udhcpc -i eth0 -s /usr/share/udhcpc/default.script
EOF
chmod +x usr/bin/connect

echo "✅ Networking configured. Type 'connect' to get online."

# 2. Package Manager (phazepkg)
# ----------------------------------------------------------------
echo "📦 Creating Package Manager (phazepkg)..."
mkdir -p usr/bin var/lib/phazepkg

cat > usr/bin/phazepkg << 'EOF'
#!/bin/sh
# PhazeOS Simple Package Manager
DB_DIR="/var/lib/phazepkg"

case "$1" in
    install)
        PKG="$2"
        if [ -z "$PKG" ]; then echo "Usage: phazepkg install <package.tar.gz>"; exit 1; fi
        echo "Installing $PKG..."
        tar -C / -xf "$PKG"
        NAME=$(basename "$PKG")
        date > "$DB_DIR/$NAME.installed"
        echo "✅ Installed $NAME"
        ;;
    list)
        ls "$DB_DIR"
        ;;
    *)
        echo "Usage: phazepkg {install|list}"
        exit 1
        ;;
esac
EOF
chmod +x usr/bin/phazepkg

echo "✅ phazepkg installed."

# 3. Final Polish
# ----------------------------------------------------------------
echo "✨ Final Polish..."
echo "phazeos" > etc/hostname
# Ensure /etc/resolv.conf exists
touch etc/resolv.conf

echo ""
echo "=========================================="
echo "✅ PHASE 1 COMPLETE"
echo "=========================================="
echo "Networking: OK (use 'connect' command)"
echo "Pkg Manager: OK (phazepkg)"
echo ""
echo "Now rebuilding the Master VDI..."
./16-build-vdi-disk.sh
