#!/bin/bash
# Build and install PhazeOS Desktop Shell

set -e

echo "🔨 Building PhazeOS Desktop Shell..."

cd server

# Get dependencies
echo "📦 Getting dependencies..."
go get github.com/gorilla/websocket

# Build
echo "🏗️ Compiling..."
go build -o phazeos-shell main.go

echo "✅ Build complete!"
echo ""
echo "To run locally:"
echo "  cd server && ./phazeos-shell"
echo ""
echo "Then open browser to http://localhost:8080"
