#!/bin/bash
# PhazeVPN Build Script using CMake

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
INSTALL_DIR="${SCRIPT_DIR}/install"

echo "=========================================="
echo "PhazeVPN CMake Build Script"
echo "=========================================="
echo ""

# Parse command line arguments
BUILD_TYPE="Release"
INSTALL_TO_SYSTEM=false
BUILD_PROTOCOL_GO=true
BUILD_WEB_PORTAL=true
BUILD_PROTOCOL_PYTHON=true
BUILD_BROWSER=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --install-system)
            INSTALL_TO_SYSTEM=true
            shift
            ;;
        --no-protocol-go)
            BUILD_PROTOCOL_GO=false
            shift
            ;;
        --no-web-portal)
            BUILD_WEB_PORTAL=false
            shift
            ;;
        --no-protocol-python)
            BUILD_PROTOCOL_PYTHON=false
            shift
            ;;
        --no-browser)
            BUILD_BROWSER=false
            shift
            ;;
        --clean)
            echo "Cleaning build directory..."
            rm -rf "${BUILD_DIR}"
            rm -rf "${INSTALL_DIR}"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --debug              Build in Debug mode (default: Release)"
            echo "  --install-system     Install to system directories (/opt/phaze-vpn)"
            echo "  --no-protocol-go     Don't build Go protocol server"
            echo "  --no-web-portal      Don't build web portal"
            echo "  --no-protocol-python Don't build Python protocol server"
            echo "  --no-browser         Don't build browser"
            echo "  --clean              Clean build directory before building"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check for CMake
if ! command -v cmake &> /dev/null; then
    echo "❌ Error: CMake is not installed"
    echo "Install with: sudo apt-get install cmake"
    exit 1
fi

# Create build directory
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Configure CMake
echo ""
echo "Configuring CMake..."
CMAKE_ARGS=(
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
    -DBUILD_PROTOCOL_GO="${BUILD_PROTOCOL_GO}"
    -DBUILD_WEB_PORTAL="${BUILD_WEB_PORTAL}"
    -DBUILD_PROTOCOL_PYTHON="${BUILD_PROTOCOL_PYTHON}"
    -DBUILD_BROWSER="${BUILD_BROWSER}"
    -DINSTALL_SYSTEMD_SERVICES=ON
)

if [ "$INSTALL_TO_SYSTEM" = true ]; then
    CMAKE_ARGS+=(-DINSTALL_TO_SYSTEM=ON)
    CMAKE_ARGS+=(-DCMAKE_INSTALL_PREFIX=/opt/phaze-vpn)
else
    CMAKE_ARGS+=(-DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}")
fi

cmake "${SCRIPT_DIR}" "${CMAKE_ARGS[@]}"

# Build
echo ""
echo "Building..."
cmake --build . --config "${BUILD_TYPE}" -j$(nproc)

echo ""
echo "✅ Build complete!"
echo ""
echo "To install, run:"
if [ "$INSTALL_TO_SYSTEM" = true ]; then
    echo "  sudo cmake --install ."
else
    echo "  cmake --install ."
fi
echo ""
echo "Build directory: ${BUILD_DIR}"
echo "Install directory: ${INSTALL_DIR}"

