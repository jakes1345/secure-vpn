#!/bin/bash
# PhazeOS - Phase 2 Readiness Test
# Compiles a dynamic binary to ensure Glibc is working correctly.

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
TARGET_GCC="$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-gcc"
TEST_DIR="$PHAZEOS/usr/bin"

echo "=========================================="
echo "  PHASE 2: READINESS TEST"
echo "=========================================="

# 1. Create Source
echo "📝 Creating test source code..."
cat > test_dynamic.c << 'EOF'
#include <stdio.h>
#include <math.h>

int main() {
    printf("======================================\n");
    printf("  PHASE 2 UNLOCKED: DYNAMIC LINKING OK\n");
    printf("  Math Check: sqrt(1337) = %.2f\n", sqrt(1337));
    printf("======================================\n");
    return 0;
}
EOF

# 2. Compile Dynamically (using shared libs)
echo "🔨 Compiling dynamic binary..."
$TARGET_GCC test_dynamic.c -o $TEST_DIR/test-phase2 -lm

# 3. Check Dependencies
echo "🔍 Checking dependencies..."
$PHAZEOS/toolchain/bin/x86_64-phazeos-linux-gnu-readelf -d $TEST_DIR/test-phase2 | grep NEEDED

# 4. Cleanup
rm test_dynamic.c

echo ""
echo "✅ Test binary created at: /usr/bin/test-phase2"
echo "Rebuilding VDI to include it..."

./16-build-vdi-disk.sh
