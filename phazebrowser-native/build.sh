#!/bin/bash

# PhazeBrowser Native Build Script

set -e

echo "🔍 Checking dependencies..."

# Check for CMake
if ! command -v cmake &> /dev/null; then
    echo "❌ CMake not found. Installing..."
    echo "Please run: sudo apt-get install cmake build-essential"
    exit 1
fi

# Check for Qt6
if [ ! -f "/usr/lib/x86_64-linux-gnu/cmake/Qt6/Qt6Config.cmake" ] && [ ! -f "/usr/lib/cmake/Qt6/Qt6Config.cmake" ]; then
    echo "❌ Qt6 not found."
    echo ""
    echo "Please install Qt6 packages:"
    echo "  sudo apt-get install qt6-base-dev qt6-webengine-dev cmake build-essential"
    exit 1
fi

echo "✅ Dependencies found!"
echo ""
echo "🔨 Building PhazeBrowser..."

# Create build directory
mkdir -p build
cd build

# Configure
echo "📋 Configuring CMake..."
cmake .. || {
    echo "❌ CMake configuration failed!"
    echo ""
    echo "Make sure Qt6 is installed:"
    echo "  sudo apt-get install qt6-base-dev qt6-webengine-dev cmake build-essential"
    exit 1
}

# Build
echo "🔨 Compiling..."
make -j$(nproc) || {
    echo "❌ Build failed!"
    exit 1
}

echo ""
echo "✅ Build successful!"
echo ""
echo "🚀 To run the browser:"
echo "  ./build/phazebrowser"
echo ""
echo "📦 To install:"
echo "  sudo make install"
echo ""
