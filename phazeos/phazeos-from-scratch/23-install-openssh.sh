#!/bin/bash
# PhazeOS - Phase 2.2: OpenSSH
# Adds remote access capabilities.

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
LOGS=$PHAZEOS/build-logs
target="x86_64-phazeos-linux-gnu"

export PATH=$PHAZEOS/toolchain/bin:$PATH
export CC=$target-gcc
export LDFLAGS="-L$PHAZEOS/usr/lib"
export CPPFLAGS="-I$PHAZEOS/usr/include"
export LIBS="-lz -ldl -lpthread"
export PKG_CONFIG_PATH="$PHAZEOS/usr/lib/pkgconfig"

echo "=========================================="
echo "  BUILDING OPENSSH"
echo "=========================================="

# 1. Download OpenSSH
VERSION="9.6p1"
FILE="openssh-9.6p1.tar.gz"
URL="https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/$FILE"

cd $SOURCES
if [ ! -f "$FILE" ]; then
    echo "⬇️  Downloading OpenSSH $VERSION..."
    wget "$URL" || { echo "❌ Failed to download OpenSSH"; exit 1; }
fi

# 2. Setup Users/Dirs
echo "🔧 Configuring SSH privileges..."
# Check if sshd user exists in the target /etc/passwd
if ! grep -q "^sshd:" $PHAZEOS/etc/passwd; then
    echo "sshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/usr/bin/false" >> $PHAZEOS/etc/passwd
    echo "sshd:x:74:" >> $PHAZEOS/etc/group
fi

mkdir -pv $PHAZEOS/var/empty/sshd
chmod 700 $PHAZEOS/var/empty/sshd

# 3. Build it
cd $BUILD
rm -rf openssh-$VERSION
tar -xf $SOURCES/$FILE
cd openssh-$VERSION

echo "🔨 Configuring..."
./configure \
    --host=$target \
    --prefix=/usr \
    --sysconfdir=/etc/ssh \
    --disable-strip \
    --with-ssl-dir=$PHAZEOS/usr \
    --with-zlib=$PHAZEOS/usr \
    --with-privsep-path=/var/empty/sshd \
    --with-privsep-user=sshd \
    --without-pam \
    2>&1 | tee $LOGS/phase2-openssh-config.log

echo "🔨 Compiling..."
make -j$(nproc) 2>&1 | tee $LOGS/phase2-openssh-make.log

echo "📦 Installing..."
make DESTDIR=$PHAZEOS install-nokeys 2>&1 | tee $LOGS/phase2-openssh-install.log

# 4. Configuration
echo "⚙️  Setting up default config..."
mkdir -p $PHAZEOS/etc/ssh
cat > $PHAZEOS/etc/ssh/sshd_config << 'EOF'
Port 22
PermitRootLogin yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication yes
ChallengeResponseAuthentication no
UsePAM no
Subsystem sftp /usr/libexec/sftp-server
EOF

# 5. Init Script (Simple)
mkdir -p $PHAZEOS/etc/init.d
cat > $PHAZEOS/etc/init.d/sshd << 'EOF'
#!/bin/sh
# Generate keys if missing
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    echo "Generating SSH keys..."
    ssh-keygen -A
fi
echo "Starting SSHD..."
/usr/sbin/sshd
EOF
chmod +x $PHAZEOS/etc/init.d/sshd

cd $BUILD
rm -rf openssh-$VERSION
echo "✅ OpenSSH Installed!"
if [ "$1" != "--no-rebuild-disk" ]; then
    echo "Rebuilding disk image..."
    $PHAZEOS/16-build-vdi-disk.sh
fi
