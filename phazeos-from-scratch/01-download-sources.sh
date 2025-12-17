#!/bin/bash
# PhazeOS From Scratch - Source Package Download
# Downloads all required source packages

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
mkdir -p $SOURCES

echo "=========================================="
echo "  DOWNLOADING SOURCE PACKAGES"
echo "=========================================="
echo ""

cd $SOURCES

# Define package versions (LFS 12.1 stable)
LINUX_VERSION="6.7.4"
GLIBC_VERSION="2.39"
GCC_VERSION="13.2.0"
BINUTILS_VERSION="2.42"
BUSYBOX_VERSION="1.36.1"
BASH_VERSION="5.2.21"

echo "📦 Downloading toolchain sources..."

# Linux Kernel
echo "⬇️  Linux kernel $LINUX_VERSION..."
wget -nc https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-$LINUX_VERSION.tar.xz

# GCC
echo "⬇️  GCC $GCC_VERSION..."
wget -nc https://ftp.gnu.org/gnu/gcc/gcc-$GCC_VERSION/gcc-$GCC_VERSION.tar.xz

# Binutils
echo "⬇️  Binutils $BINUTILS_VERSION..."
wget -nc https://ftp.gnu.org/gnu/binutils/binutils-$BINUTILS_VERSION.tar.xz

# Glibc
echo "⬇️  Glibc $GLIBC_VERSION..."
wget -nc https://ftp.gnu.org/gnu/glibc/glibc-$GLIBC_VERSION.tar.xz

# BusyBox
echo "⬇️  BusyBox $BUSYBOX_VERSION..."
wget -nc https://busybox.net/downloads/busybox-$BUSYBOX_VERSION.tar.bz2

# Bash
echo "⬇️  Bash $BASH_VERSION..."
wget -nc https://ftp.gnu.org/gnu/bash/bash-$BASH_VERSION.tar.gz

# Essential tools
echo "📦 Downloading base system tools..."

# Coreutils
wget -nc https://ftp.gnu.org/gnu/coreutils/coreutils-9.4.tar.xz

# Make
wget -nc https://ftp.gnu.org/gnu/make/make-4.4.1.tar.gz

# Grep
wget -nc https://ftp.gnu.org/gnu/grep/grep-3.11.tar.xz

# Sed
wget -nc https://ftp.gnu.org/gnu/sed/sed-4.9.tar.xz

# Gawk
wget -nc https://ftp.gnu.org/gnu/gawk/gawk-5.3.0.tar.xz

# Findutils
wget -nc https://ftp.gnu.org/gnu/findutils/findutils-4.9.0.tar.xz

# Diffutils
wget -nc https://ftp.gnu.org/gnu/diffutils/diffutils-3.10.tar.xz

# Tar
wget -nc https://ftp.gnu.org/gnu/tar/tar-1.35.tar.xz

# Gzip
wget -nc https://ftp.gnu.org/gnu/gzip/gzip-1.13.tar.xz

# Bzip2
wget -nc https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz

# XZ Utils
wget -nc https://github.com/tukaani-project/xz/releases/download/v5.4.6/xz-5.4.6.tar.xz

# Zstd
wget -nc https://github.com/facebook/zstd/releases/download/v1.5.5/zstd-1.5.5.tar.gz

# Ncurses
wget -nc https://ftp.gnu.org/gnu/ncurses/ncurses-6.4.tar.gz

# Perl
wget -nc https://www.cpan.org/src/5.0/perl-5.38.2.tar.xz

# Python
wget -nc https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tar.xz

echo ""
echo "✅ All source packages downloaded!"
echo ""

# Create checksums
echo "🔐 Generating checksums..."
sha256sum *.tar.* > SHA256SUMS
echo "✅ Checksums saved to SHA256SUMS"

echo ""
echo "=========================================="
echo "✅ DOWNLOAD COMPLETE!"
echo "=========================================="
echo ""
echo "Next step: ./02-build-toolchain.sh"
echo ""
