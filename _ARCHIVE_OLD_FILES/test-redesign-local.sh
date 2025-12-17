#!/bin/bash
# Test the website redesign locally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/web-portal"

echo "=========================================="
echo "Testing PhazeVPN Website Redesign"
echo "=========================================="
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3 install flask --user 2>/dev/null || {
        echo "❌ Could not install Flask automatically"
        echo ""
        echo "Please install Flask manually:"
        echo "  pip3 install flask"
        echo ""
        echo "Or test on VPS instead (recommended)"
        exit 1
    }
fi

# Check if templates exist
if [ ! -f "templates/base.html" ]; then
    echo "❌ Error: templates/base.html not found"
    exit 1
fi

if [ ! -f "templates/home.html" ]; then
    echo "❌ Error: templates/home.html not found"
    exit 1
fi

if [ ! -f "static/css/style.css" ]; then
    echo "❌ Error: static/css/style.css not found"
    exit 1
fi

echo "✅ All files found"
echo ""
echo "Starting web server..."
echo ""
echo "🌐 Open in browser: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run Flask app
python3 app.py

