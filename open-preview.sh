#!/bin/bash
# Open webmail preview in browser

PREVIEW_FILE="/opt/phaze-vpn/webmail-preview.html"

if [ -f "$PREVIEW_FILE" ]; then
    echo "Opening webmail preview..."
    
    # Try different browsers
    if command -v xdg-open &> /dev/null; then
        xdg-open "$PREVIEW_FILE"
    elif command -v open &> /dev/null; then
        open "$PREVIEW_FILE"
    elif command -v firefox &> /dev/null; then
        firefox "$PREVIEW_FILE" &
    elif command -v chromium &> /dev/null; then
        chromium "$PREVIEW_FILE" &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "$PREVIEW_FILE" &
    else
        echo "Please open this file in your browser:"
        echo "$PREVIEW_FILE"
    fi
else
    echo "Preview file not found: $PREVIEW_FILE"
fi

