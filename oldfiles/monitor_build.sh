#!/bin/bash
# Monitor PhazeOS build and notify when complete

BUILD_LOG="/media/jack/Liunux/secure-vpn/phazeos_build.log"
BUILD_PID=$(pgrep -f "build_phazeos_iso.sh")

echo "🔍 Monitoring PhazeOS build (PID: $BUILD_PID)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait for build to complete
while kill -0 $BUILD_PID 2>/dev/null; do
    sleep 30
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 BUILD COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if successful
if grep -q "SUCCESS! PhazeOS ISO Created!" "$BUILD_LOG"; then
    ISO_FILE=$(grep "File:" "$BUILD_LOG" | tail -1 | awk '{print $3}')
    ISO_SIZE=$(grep "Size:" "$BUILD_LOG" | tail -1 | awk '{print $3}')
    
    echo "✅ ISO CREATED SUCCESSFULLY!"
    echo ""
    echo "📦 File: $ISO_FILE"
    echo "💾 Size: $ISO_SIZE"
    echo ""
    echo "Next Steps:"
    echo "  1. Test in QEMU: ./quick_test_iso.sh"
    echo "  2. Burn to USB: sudo dd if=$ISO_FILE of=/dev/sdX bs=4M status=progress"
    echo ""
    
    # Desktop notification
    notify-send -u normal -i drive-harddisk "PhazeOS Build Complete!" "ISO created successfully: $ISO_SIZE"
else
    echo "❌ BUILD FAILED!"
    echo ""
    echo "Check errors:"
    echo "  tail -100 $BUILD_LOG"
    echo ""
    
    # Desktop notification
    notify-send -u critical -i dialog-error "PhazeOS Build Failed!" "Check build log for errors"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
