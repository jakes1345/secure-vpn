#!/bin/bash
# PhazeOS Build Progress Monitor

echo "=========================================="
echo "    PHAZEOS BUILD PROGRESS MONITOR"
echo "=========================================="
echo ""

LOG_FILE="/media/jack/Liunux/secure-vpn/phazeos_rebuild.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "⏳ Build hasn't started logging yet..."
    echo "Checking if build process is running..."
    if pgrep -f "rebuild_iso_quick" > /dev/null; then
        echo "✅ Build process is running!"
    else
        echo "❌ Build process not found"
    fi
    exit 0
fi

echo "📊 Last 30 lines of build log:"
echo "=========================================="
tail -n 30 "$LOG_FILE"
echo "=========================================="
echo ""

# Check for ISO file first (best indicator of success)
ISO_FILE=$(find /media/jack/Liunux/secure-vpn/phazeos-build/out/ -name "*.iso" 2>/dev/null | head -1)

# Check for completion markers
if [ -n "$ISO_FILE" ] && [ -f "$ISO_FILE" ]; then
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    echo "✅ BUILD COMPLETE!"
    echo "📦 ISO File: $ISO_FILE"
    echo "💾 Size: $ISO_SIZE"
    # Check for actual errors (excluding package names and warnings)
    ACTUAL_ERRORS=$(grep -iE "(error|failed|fatal)" "$LOG_FILE" 2>/dev/null | grep -vE "(libgpg-error|perl-error|xcb-util-errors|downloading|installing|Packages)" | grep -vE "WARNING.*firmware" | wc -l)
    if [ "$ACTUAL_ERRORS" -gt 0 ]; then
        echo "⚠️  Note: Some warnings detected, but ISO was created successfully"
    fi
elif grep -q "SUCCESS" "$LOG_FILE" 2>/dev/null; then
    echo "✅ BUILD COMPLETE!"
    if [ -n "$ISO_FILE" ]; then
        ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
        echo "📦 ISO File: $ISO_FILE"
        echo "💾 Size: $ISO_SIZE"
    fi
elif grep -qiE "(error|failed|fatal)" "$LOG_FILE" 2>/dev/null && grep -qiE "(error|failed|fatal)" "$LOG_FILE" 2>/dev/null | grep -vE "(libgpg-error|perl-error|xcb-util-errors|downloading|installing|Packages)" | grep -qvE "WARNING.*firmware"; then
    echo "⚠️  Errors detected in build log"
    echo "Run: grep -iE '(error|failed|fatal)' $LOG_FILE | grep -vE '(libgpg-error|perl-error|xcb-util-errors|downloading|installing|Packages)'"
elif grep -q "downloading" "$LOG_FILE" 2>/dev/null; then
    echo "📥 Status: Downloading packages..."
elif grep -q "installing" "$LOG_FILE" 2>/dev/null; then
    echo "⚙️  Status: Installing packages..."
elif grep -q "xorriso\|mkarchiso.*Done" "$LOG_FILE" 2>/dev/null; then
    echo "💿 Status: Creating ISO image..."
    # Show latest xorriso progress
    grep "xorriso.*UPDATE\|mkarchiso.*INFO" "$LOG_FILE" | tail -1
else
    echo "🔄 Status: Build in progress..."
fi

echo ""
echo "Commands:"
echo "  Watch live: tail -f $LOG_FILE"
echo "  Check again: ./check_build_progress.sh"
