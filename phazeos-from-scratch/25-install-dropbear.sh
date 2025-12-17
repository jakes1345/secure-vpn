#!/bin/bash
set -e

PHAZEOS_ROOT=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
PHAZEOS=$PHAZEOS_ROOT/phazeos-root
SOURCES=$PHAZEOS_ROOT/sources
BUILD=$PHAZEOS_ROOT/build
target=x86_64-phazeos-linux-gnu

export PATH=$PHAZEOS/toolchain/bin:$PATH
export CC=$target-gcc
export AR=$target-ar
export RANLIB=$target-ranlib
export CFLAGS="-DMB_LEN_MAX=16"

# Dropbear Version
DROPBEAR_VER="dropbear-2022.83" # Using a known stable version
DROPBEAR_URL="https://matt.ucc.asn.au/dropbear/releases/${DROPBEAR_VER}.tar.bz2"

echo "=========================================="
echo "  INSTALLING DROPBEAR SSH (Alternative)"
echo "=========================================="

mkdir -p $SOURCES $BUILD

# 1. Download
cd $SOURCES
if [ ! -f "${DROPBEAR_VER}.tar.bz2" ]; then
    echo "⬇️  Downloading Dropbear..."
    wget "$DROPBEAR_URL"
fi

# 2. Build
echo "🔨 Building Dropbear..."
cd $BUILD
rm -rf $DROPBEAR_VER
tar -xf $SOURCES/${DROPBEAR_VER}.tar.bz2
cd $DROPBEAR_VER

# Configure
./configure --prefix=/usr --host=$target --disable-zlib --disable-wtmp --disable-lastlog

# Disable Password Auth (Missing libcrypt) - Use Keys Only
cat > localoptions.h <<EOF
#define DROPBEAR_SVR_PASSWORD_AUTH 0
#define DROPBEAR_CLI_PASSWORD_AUTH 0
EOF

# Build
make PROGRAMS="dropbear dbclient dropbearkey scp" -j$(nproc)
make PROGRAMS="dropbear dbclient dropbearkey scp" DESTDIR=$PHAZEOS install

# 3. Configuration
echo "⚙️  Configuring Dropbear..."
mkdir -p $PHAZEOS/etc/dropbear
mkdir -p $PHAZEOS/etc/init.d

# Generate host keys (This usually needs to be done ON DEVICE on first boot, 
# but we can pre-generate them or add a script to generate them)
# We will add a startup script that transforms into the key generator if keys are missing.

cat > $PHAZEOS/etc/init.d/S50dropbear << 'EOF'
#!/bin/sh
# Start Dropbear SSH

# Generate keys if missing
if [ ! -f /etc/dropbear/dropbear_rsa_host_key ]; then
    echo "Generating Dropbear RSA key..."
    mkdir -p /etc/dropbear
    dropbearkey -t rsa -f /etc/dropbear/dropbear_rsa_host_key
fi
if [ ! -f /etc/dropbear/dropbear_ecdsa_host_key ]; then
    echo "Generating Dropbear ECDSA key..."
    dropbearkey -t ecdsa -f /etc/dropbear/dropbear_ecdsa_host_key
fi

# Start Server
# -R = create host keys if missing (handled above mainly)
# -E = log to stderr (useful for testing) or syslog
# -B = allow blank passwords (optional, for testing)
echo "Starting Dropbear SSH..."
/usr/sbin/dropbear -R -B
EOF

chmod +x $PHAZEOS/etc/init.d/S50dropbear

# Ensure /usr/sbin exists (Dropbear installs there by default usually)
# Actually configure --prefix=/usr puts binaries in /usr/bin or /usr/sbin?
# Dropbear make install puts 'dropbear' in sbin and others in bin.

echo "✅ Dropbear Installed!"
