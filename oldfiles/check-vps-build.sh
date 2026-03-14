#!/bin/bash
# Quick script to check PhazeOS build progress on VPS

echo "=========================================="
echo "📊 PhazeOS VPS Build Status"
echo "=========================================="
echo ""

ssh root@15.204.11.19 'bash -s' << 'EOFREMOTE'

# Check if build is running
if ps aux | grep -q "[b]uild-robust.sh"; then
    echo "✅ Build is RUNNING"
    echo ""
else
    echo "⚠️  Build process not found"
    echo ""
fi

# Show last 30 lines of log
echo "📝 Latest build output:"
echo "----------------------------------------"
tail -30 /root/phazeos-build/build-vps.log
echo "----------------------------------------"
echo ""

# Show what's been built
echo "📦 Installed binaries:"
ls -1 /root/phazeos-build/usr/bin 2>/dev/null | wc -l
echo ""

echo "📚 Installed libraries:"
find /root/phazeos-build/usr/lib -name '*.so*' 2>/dev/null | wc -l
echo ""

# Disk usage
echo "💾 Build directory size:"
du -sh /root/phazeos-build

EOFREMOTE

echo ""
echo "=========================================="
echo "To monitor live:"
echo "  ssh root@15.204.11.19"
echo "  screen -r phazeos-build"
echo "=========================================="
