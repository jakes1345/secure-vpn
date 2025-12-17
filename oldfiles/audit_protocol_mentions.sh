#!/bin/bash
#
# Audit all HTML files for accurate VPN protocol information
#

echo "🔍 Auditing all HTML files for VPN protocol mentions..."
echo ""

cd /media/jack/Liunux/secure-vpn/web-portal/templates

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Files mentioning VPN protocols:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -l "protocol\|OpenVPN\|WireGuard\|PhazeVPN" *.html | while read file; do
    echo ""
    echo "📄 $file:"
    grep -n "protocol\|OpenVPN\|WireGuard\|PhazeVPN" "$file" | head -5
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Files that need updating:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for files that mention only 1 or 2 protocols
echo ""
echo "Files mentioning only OpenVPN or WireGuard (need to add PhazeVPN):"
grep -l "OpenVPN\|WireGuard" *.html | while read file; do
    if ! grep -q "PhazeVPN" "$file"; then
        echo "  ⚠️  $file - Missing PhazeVPN protocol mention"
    fi
done

echo ""
echo "Files with vague 'protocols' mention (need to be specific):"
grep -l "protocols" *.html | while read file; do
    # Check if it mentions specific protocols
    if ! grep -q "OpenVPN.*WireGuard.*PhazeVPN\|three.*protocol" "$file"; then
        echo "  ⚠️  $file - Has vague 'protocols' mention"
        grep -n "protocol" "$file" | head -3
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=$(grep -l "protocol\|OpenVPN\|WireGuard" *.html | wc -l)
COMPLETE=$(grep -l "OpenVPN.*WireGuard.*PhazeVPN\|three.*protocol\|Triple.*Protocol" *.html | wc -l)

echo ""
echo "Total files mentioning protocols: $TOTAL"
echo "Files with all 3 protocols mentioned: $COMPLETE"
echo "Files needing updates: $((TOTAL - COMPLETE))"
echo ""

if [ $((TOTAL - COMPLETE)) -gt 0 ]; then
    echo "⚠️  Some files need updating to mention all 3 protocols"
else
    echo "✅ All files mention all 3 protocols!"
fi
