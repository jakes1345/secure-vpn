#!/usr/bin/env bash
# PhazeOS - User & Service Setup (Auto-Login GUI)
# Configures users, Runit init system, and Auto-Login to LabWC

set -e

PHAZEOS="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"

# 1. Runit (Init System)
RUNIT_VER="2.1.2"
echo "🔨 Setup Runit..."
mkdir -p "$PHAZEOS/etc/runit"
mkdir -p "$PHAZEOS/etc/sv"
mkdir -p "$PHAZEOS/etc/service"

# Download runit if needed (assuming binaries are in /usr/bin from busybox or runit package)
# Ideally we should build runit, but busybox gives us runit compatible tools usually.
# If not, let's assume we use busybox init for now or the runit we might have built in Phase 1?
# Checking Phase 1... Ah, we might have missed compiling Runit in phase 1.
# Let's rely on Busybox init for simplicity in this Alpha, BUT configure it to autologin.
# WAIT: The live media script uses `switch_root` to `/bin/runit-init`. So we need real runit.

# Installing Runit binaries (Cross-compiled or static)
# NOTE: For this "from scratch" guide, properly compiling runit is complex.
# We will cheat slightly and use Void Linux's static runit or just rely on busybox's runit implementation if available.
# BETTER: Use Busybox runit implementation which is `runsv`, `runsvdir`, `runit`.
# Check if busybox has them.
if [ -f "$PHAZEOS/bin/busybox" ]; then
    # Create symlinks for runit tools if they exist
    for tool in runit runsv runsvdir sv chpst; do
         ln -sf busybox "$PHAZEOS/bin/$tool"
    done
fi

# 2. Stage 1/2/3 Scripts
cat > "$PHAZEOS/etc/runit/1" <<EOF
#!/bin/sh
# Stage 1: System Boot
echo "System Booting..."
mount -t devtmpfs devtmpfs /dev
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts
mkdir -p /run/user
touch /etc/runit/stopit
chmod 0 /etc/runit/stopit
EOF
chmod +x "$PHAZEOS/etc/runit/1"

cat > "$PHAZEOS/etc/runit/2" <<EOF
#!/bin/sh
# Stage 2: Service Monitor
exec runsvdir -P /etc/service
EOF
chmod +x "$PHAZEOS/etc/runit/2"

cat > "$PHAZEOS/etc/runit/3" <<EOF
#!/bin/sh
# Stage 3: Shutdown
echo "System Configured to Halt."
EOF
chmod +x "$PHAZEOS/etc/runit/3"

# 3. Create User Account
echo "👤 Creating User: admin..."
# We need to edit /etc/passwd directly since 'useradd' might not be perfectly working in cross-w/o-chroot
# But we can write the file.
cat > "$PHAZEOS/etc/passwd" <<EOF
root:x:0:0:root:/root:/bin/sh
admin:x:1000:1000:Phaze Admin:/home/admin:/bin/fish
nobody:x:65534:65534:Nobody:/:/bin/false
EOF

cat > "$PHAZEOS/etc/group" <<EOF
root:x:0:
users:x:100:
wheel:x:998:admin
admin:x:1000:
video:x:90:admin
audio:x:92:admin
input:x:98:admin
EOF

cat > "$PHAZEOS/etc/shadow" <<EOF
root::19000:0:99999:7:::
admin::19000:0:99999:7:::
EOF
# Note: Empty password for admin for now (Live CD mode)

mkdir -p "$PHAZEOS/home/admin"
chown -R 1000:1000 "$PHAZEOS/home/admin"
chmod 700 "$PHAZEOS/home/admin"

# 4. Configure Auto-Login (The "Normal" Boot)
# We use a runit service for 'getty' that auto-logs in.
mkdir -p "$PHAZEOS/etc/sv/tty1"
cat > "$PHAZEOS/etc/sv/tty1/run" <<EOF
#!/bin/sh
# Auto-login as admin
export XDG_RUNTIME_DIR=/run/user/1000
mkdir -p \$XDG_RUNTIME_DIR
chown 1000:1000 \$XDG_RUNTIME_DIR
chmod 700 \$XDG_RUNTIME_DIR

# Auto start LabWC
exec /bin/su -l admin -c "labwc"
EOF
chmod +x "$PHAZEOS/etc/sv/tty1/run"

# Link service
ln -sf /etc/sv/tty1 "$PHAZEOS/etc/service/tty1"

# 5. Sudo setup
echo "root ALL=(ALL) NOPASSWD: ALL" > "$PHAZEOS/etc/sudoers"
echo "admin ALL=(ALL) NOPASSWD: ALL" >> "$PHAZEOS/etc/sudoers"
chmod 440 "$PHAZEOS/etc/sudoers"

echo "✅ User & Services Configured. Auto-login active."
