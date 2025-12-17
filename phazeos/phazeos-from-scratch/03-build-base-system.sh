#!/bin/bash
# PhazeOS From Scratch - Base System Build
# Compiles all essential system utilities

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
LOGS=$PHAZEOS/build-logs
MAKEFLAGS="-j$(nproc)"

export PATH=$PHAZEOS/toolchain/bin:$PATH

echo "=========================================="
echo "  BUILDING PHAZEOS BASE SYSTEM"
echo "=========================================="
echo ""
echo "This will take 2-4 hours depending on your system."
echo ""

cd $BUILD

# Helper function to build packages
build_package() {
    local NAME=$1
    local VERSION=$2
    local TARBALL=$3
    local CONFIG_CMD=$4
    
    echo "🔨 Building $NAME $VERSION..."
    
    tar -xf $SOURCES/$TARBALL || { echo "❌ Failed to extract $NAME"; return 1; }
    cd $NAME-$VERSION
    
    eval $CONFIG_CMD 2>&1 | tee $LOGS/base-$NAME-configure.log
    if [ $? -ne 0 ]; then
        echo "⚠️  Configure failed for $NAME, skipping..."
        cd $BUILD
        rm -rf $NAME-$VERSION
        return 1
    fi
    
    make $MAKEFLAGS 2>&1 | tee $LOGS/base-$NAME-make.log || { echo "❌ Make failed for $NAME"; cd $BUILD; rm -rf $NAME-$VERSION; return 1; }
    make DESTDIR=$PHAZEOS install 2>&1 | tee $LOGS/base-$NAME-install.log || { echo "❌ Install failed for $NAME"; cd $BUILD; rm -rf $NAME-$VERSION; return 1; }
    
    cd $BUILD
    rm -rf $NAME-$VERSION
    echo "✅ $NAME complete!"
    echo ""
}

# ============================================
# ESSENTIAL UTILITIES
# ============================================

# Bash - The shell
build_package "bash" "5.2.21" "bash-5.2.21.tar.gz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# Coreutils - Essential file/text/shell utilities
build_package "coreutils" "9.4" "coreutils-9.4.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu --enable-install-program=hostname"

# Findutils - find, locate, xargs
build_package "findutils" "4.9.0" "findutils-4.9.0.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# Grep - Pattern matching
build_package "grep" "3.11" "grep-3.11.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# Sed - Stream editor
build_package "sed" "4.9" "sed-4.9.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# Gawk - AWK implementation
build_package "gawk" "5.3.0" "gawk-5.3.0.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# Diffutils - diff, cmp, diff3, sdiff
build_package "diffutils" "3.10" "diffutils-3.10.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# ============================================
# COMPRESSION TOOLS
# ============================================

# Gzip
build_package "gzip" "1.13" "gzip-1.13.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# Bzip2
echo "🔨 Building Bzip2..."
tar -xf $SOURCES/bzip2-1.0.8.tar.gz
cd bzip2-1.0.8
make -f Makefile-libbz2_so CC=x86_64-phazeos-linux-gnu-gcc 2>&1 | tee $LOGS/base-bzip2-make.log
make clean
make CC=x86_64-phazeos-linux-gnu-gcc 2>&1 | tee -a $LOGS/base-bzip2-make.log
make PREFIX=$PHAZEOS/usr install 2>&1 | tee $LOGS/base-bzip2-install.log
cd $BUILD
rm -rf bzip2-1.0.8
echo "✅ Bzip2 complete!"
echo ""

# XZ Utils
build_package "xz" "5.4.6" "xz-5.4.6.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# Zstd
echo "🔨 Building Zstd..."
tar -xf $SOURCES/zstd-1.5.5.tar.gz
cd zstd-1.5.5
make CC=x86_64-phazeos-linux-gnu-gcc $MAKEFLAGS 2>&1 | tee $LOGS/base-zstd-make.log
make PREFIX=$PHAZEOS/usr install 2>&1 | tee $LOGS/base-zstd-install.log
cd $BUILD
rm -rf zstd-1.5.5
echo "✅ Zstd complete!"
echo ""

# Tar
build_package "tar" "1.35" "tar-1.35.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu"

# ============================================
# DEVELOPMENT TOOLS
# ============================================

# Make
build_package "make" "4.4.1" "make-4.4.1.tar.gz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu --without-guile"

# Ncurses - Terminal handling library
build_package "ncurses" "6.4" "ncurses-6.4.tar.gz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu --with-shared --without-debug --enable-widec --enable-pc-files"

# Perl
echo "🔨 Building Perl..."
tar -xf $SOURCES/perl-5.38.2.tar.xz
cd perl-5.38.2
./Configure -des \
    -Dprefix=/usr \
    -Dvendorprefix=/usr \
    -Dprivlib=/usr/lib/perl5/5.38/core_perl \
    -Darchlib=/usr/lib/perl5/5.38/core_perl \
    -Dsitelib=/usr/lib/perl5/5.38/site_perl \
    -Dsitearch=/usr/lib/perl5/5.38/site_perl \
    -Dvendorlib=/usr/lib/perl5/5.38/vendor_perl \
    -Dvendorarch=/usr/lib/perl5/5.38/vendor_perl 2>&1 | tee $LOGS/base-perl-configure.log
make $MAKEFLAGS 2>&1 | tee $LOGS/base-perl-make.log
make DESTDIR=$PHAZEOS install 2>&1 | tee $LOGS/base-perl-install.log
cd $BUILD
rm -rf perl-5.38.2
echo "✅ Perl complete!"
echo ""

# Python
build_package "Python" "3.12.2" "Python-3.12.2.tar.xz" \
    "./configure --prefix=/usr --host=x86_64-phazeos-linux-gnu --build=x86_64-pc-linux-gnu --enable-shared --without-ensurepip"

# ============================================
# SYSTEM FILES
# ============================================

echo "📝 Creating essential system files..."

# Create /etc/passwd
cat > $PHAZEOS/etc/passwd << "EOF"
root:x:0:0:root:/root:/bin/bash
bin:x:1:1:bin:/dev/null:/usr/bin/false
daemon:x:6:6:Daemon User:/dev/null:/usr/bin/false
messagebus:x:18:18:D-Bus Message Daemon User:/run/dbus:/usr/bin/false
uuidd:x:80:80:UUID Generation Daemon User:/dev/null:/usr/bin/false
nobody:x:65534:65534:Unprivileged User:/dev/null:/usr/bin/false
EOF

# Create /etc/group
cat > $PHAZEOS/etc/group << "EOF"
root:x:0:
bin:x:1:daemon
sys:x:2:
kmem:x:3:
tape:x:4:
tty:x:5:
daemon:x:6:
floppy:x:7:
disk:x:8:
lp:x:9:
dialout:x:10:
audio:x:11:
video:x:12:
utmp:x:13:
cdrom:x:15:
adm:x:16:
messagebus:x:18:
input:x:24:
mail:x:34:
kvm:x:61:
uuidd:x:80:
wheel:x:97:
users:x:999:
nogroup:x:65534:
EOF

# Create /etc/fstab
cat > $PHAZEOS/etc/fstab << "EOF"
# file system  mount-point  type     options             dump  fsck
#                                                              order
/dev/sda1      /            ext4     defaults            1     1
proc           /proc        proc     nosuid,noexec,nodev 0     0
sysfs          /sys         sysfs    nosuid,noexec,nodev 0     0
devpts         /dev/pts     devpts   gid=5,mode=620      0     0
tmpfs          /run         tmpfs    defaults            0     0
devtmpfs       /dev         devtmpfs mode=0755,nosuid    0     0
EOF

# Create /etc/os-release
cat > $PHAZEOS/etc/os-release << "EOF"
NAME="PhazeOS"
VERSION="1.0-alpha"
ID=phazeos
PRETTY_NAME="PhazeOS 1.0 Alpha"
VERSION_ID="1.0"
HOME_URL="https://phazeos.org"
SUPPORT_URL="https://phazeos.org/support"
BUG_REPORT_URL="https://phazeos.org/bugs"
EOF

# Create /etc/hostname
echo "phazeos" > $PHAZEOS/etc/hostname

# Create /etc/hosts
cat > $PHAZEOS/etc/hosts << "EOF"
127.0.0.1  localhost phazeos
::1        localhost
EOF

echo "✅ System files created!"
echo ""

# Create essential directories
mkdir -pv $PHAZEOS/{boot,home,mnt,opt,srv}
mkdir -pv $PHAZEOS/etc/{opt,sysconfig}
mkdir -pv $PHAZEOS/lib/firmware
mkdir -pv $PHAZEOS/media/{floppy,cdrom}
mkdir -pv $PHAZEOS/usr/{,local/}{include,src}
mkdir -pv $PHAZEOS/usr/local/{bin,lib,sbin}
mkdir -pv $PHAZEOS/usr/{,local/}share/{color,dict,doc,info,locale,man}
mkdir -pv $PHAZEOS/usr/{,local/}share/{misc,terminfo,zoneinfo}
mkdir -pv $PHAZEOS/usr/{,local/}share/man/man{1..8}
mkdir -pv $PHAZEOS/var/{cache,local,log,mail,opt,spool}
mkdir -pv $PHAZEOS/var/lib/{color,misc,locate}

# Create symlinks
ln -sfv /run $PHAZEOS/var/run
ln -sfv /run/lock $PHAZEOS/var/lock

echo "✅ Directory structure created!"
echo ""

echo "=========================================="
echo "✅ BASE SYSTEM BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Next step: ./04-build-kernel.sh"
echo ""
