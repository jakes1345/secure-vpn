#!/bin/bash
# Mark all custom protocol files as experimental

echo "🔖 Marking custom protocol files as EXPERIMENTAL..."
echo ""

EXPERIMENTAL_HEADER='# ⚠️ EXPERIMENTAL / UNAUDITED
# This is a custom protocol under development.
# For production use, use OpenVPN or WireGuard.
# Status: Experimental - Not recommended for production
#'

# Find all phazevpn-protocol files
find . -path "*/phazevpn-protocol/*.py" -type f | while read file; do
    # Check if already marked
    if ! grep -q "EXPERIMENTAL / UNAUDITED" "$file" 2>/dev/null; then
        echo "  Marking: $file"
        # Add header after shebang
        if head -1 "$file" | grep -q "^#!"; then
            # Has shebang - add after it
            sed -i "1a\\
$EXPERIMENTAL_HEADER" "$file"
        else
            # No shebang - add at top
            echo "$EXPERIMENTAL_HEADER" | cat - "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        fi
    else
        echo "  Already marked: $file"
    fi
done

echo ""
echo "✅ Done! All custom protocol files marked as experimental."

