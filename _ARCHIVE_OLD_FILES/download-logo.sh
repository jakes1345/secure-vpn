#!/bin/bash
# Download logo from Grok/Imagine URL and process it

if [ -z "$1" ]; then
    echo "Usage: ./download-logo.sh <image-url>"
    echo ""
    echo "Example:"
    echo "  ./download-logo.sh 'https://imagine-public.x.ai/imagine-public/images/...'"
    echo ""
    echo "This will:"
    echo "  1. Download the image"
    echo "  2. Save as phazevpn-source.png"
    echo "  3. Resize to all sizes automatically"
    exit 1
fi

URL="$1"
OUTPUT_DIR="assets/icons"
SOURCE_FILE="$OUTPUT_DIR/phazevpn-source.png"

echo "📥 Downloading logo from AI..."
mkdir -p "$OUTPUT_DIR"

# Download with curl or wget
if command -v curl >/dev/null 2>&1; then
    curl -L -o "$SOURCE_FILE" "$URL"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$SOURCE_FILE" "$URL"
else
    echo "❌ Error: Need curl or wget to download"
    exit 1
fi

if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ Download failed!"
    exit 1
fi

echo "✅ Downloaded: $SOURCE_FILE"
echo ""
echo "🔄 Resizing to all sizes..."

# Run the resize script
python3 resize-logos.py "$SOURCE_FILE"

echo ""
echo "✅ Done! Your logo is ready to use!"

