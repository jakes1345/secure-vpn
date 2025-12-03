#!/bin/bash
# Remove duplicate/bloat files from web portal

cd "$(dirname "$0")"

echo "=========================================="
echo "🧹 REMOVING BLOAT FILES"
echo "=========================================="
echo ""

# Backup first
echo "📦 Creating backup..."
mkdir -p backups
tar -czf backups/web-portal-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
    app_secure.py app_secure_integrated.py app-original.py 2>/dev/null || true
echo "✅ Backup created"
echo ""

# Remove duplicates
echo "🗑️  Removing duplicate files..."
FILES_TO_REMOVE=(
    "app_secure.py"
    "app_secure_integrated.py"
    "app-original.py"
)

for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo "   Removing: $file"
        rm "$file"
    else
        echo "   ⚠️  $file not found (already removed?)"
    fi
done

echo ""
echo "=========================================="
echo "✅ BLOAT REMOVED"
echo "=========================================="
echo ""
echo "📝 Main app file: app.py (keep this!)"
echo "📝 Backup location: backups/"
echo ""

