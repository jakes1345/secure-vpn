#!/bin/bash
# PhazeOS From Scratch - MINIMAL Base System
# Only builds what's absolutely necessary for kernel and ISO

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
LOGS=$PHAZEOS/build-logs
MAKEFLAGS="-j$(nproc)"

export PATH=$PHAZEOS/toolchain/bin:$PATH

echo "=========================================="
echo "  BUILDING MINIMAL BASE SYSTEM"
echo "=========================================="
echo ""
echo "Building only essential packages for bootable ISO"
echo ""

cd $BUILD

# Just build BusyBox - it has everything we need!
echo "🔨 Building BusyBox (all-in-one utilities)..."
tar -xf $SOURCES/busybox-1.36.1.tar.bz2
cd busybox-1.36.1

# Configure BusyBox with everything
make defconfig
make CROSS_COMPILE=x86_64-phazeos-linux-gnu- $MAKEFLAGS 2>&1 | tee $LOGS/busybox-make.log
make CROSS_COMPILE=x86_64-phazeos-linux-gnu- CONFIG_PREFIX=$PHAZEOS install 2>&1 | tee $LOGS/busybox-install.log

cd $BUILD
rm -rf busybox-1.36.1
echo "✅ BusyBox complete!"
echo ""

# Create essential system files
echo "📝 Creating system files..."

mkdir -p $PHAZEOS/{etc,proc,sys,dev,run,tmp}
mkdir -p $PHAZEOS/{boot,home,mnt,opt,srv}
mkdir -p $PHAZEOS/usr/{bin,sbin,lib}
mkdir -p $PHAZEOS/var/{log,tmp}

# /etc/passwd
cat > $PHAZEOS/etc/passwd << "EOF"
root:x:0:0:root:/root:/bin/sh
nobody:x:65534:65534:nobody:/dev/null:/bin/false
EOF

# /etc/group
cat > $PHAZEOS/etc/group << "EOF"
root:x:0:
nogroup:x:65534:
EOF

# /etc/fstab
cat > $PHAZEOS/etc/fstab << "EOF"
# file system  mount-point  type     options             dump  fsck
proc           /proc        proc     defaults            0     0
sysfs          /sys         sysfs    defaults            0     0
devpts         /dev/pts     devpts   gid=5,mode=620      0     0
tmpfs          /run         tmpfs    defaults            0     0
devtmpfs       /dev         devtmpfs mode=0755,nosuid    0     0
EOF

# /etc/os-release
cat > $PHAZEOS/etc/os-release << "EOF"
NAME="PhazeOS"
VERSION="1.0-alpha"
ID=phazeos
PRETTY_NAME="PhazeOS 1.0 Alpha - From Scratch"
VERSION_ID="1.0"
EOF

# /etc/hostname
echo "phazeos" > $PHAZEOS/etc/hostname

# /etc/hosts
cat > $PHAZEOS/etc/hosts << "EOF"
127.0.0.1  localhost phazeos
::1        localhost
EOF

# Init script
cat > $PHAZEOS/init << "EOF"
#!/bin/sh
# PhazeOS Init

/bin/mount -t proc proc /proc
/bin/mount -t sysfs sysfs /sys
/bin/mount -t devtmpfs devtmpfs /dev

echo "Welcome to PhazeOS!"
echo "Built from scratch $(date)"

exec /bin/sh
EOF

chmod +x $PHAZEOS/init

echo "✅ System files created!"
echo ""

echo "=========================================="
echo "✅ MINIMAL BASE SYSTEM COMPLETE!"
echo "=========================================="
echo ""
echo "Next step: ./04-build-kernel.sh"
echo ""
