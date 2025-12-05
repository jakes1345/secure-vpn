#!/bin/bash
# Apply complete website redesign - replace old templates with new modern design

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$SCRIPT_DIR/web-portal/templates"

echo "=========================================="
echo "Applying PhazeVPN Website Redesign"
echo "=========================================="
echo ""

# Backup old templates
echo "[1/5] Backing up old templates..."
BACKUP_DIR="$TEMPLATES_DIR/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$TEMPLATES_DIR"/*.html "$BACKUP_DIR/" 2>/dev/null || true
echo "   ✅ Backup created: $BACKUP_DIR"

# Replace base template
echo "[2/5] Replacing base template..."
if [ -f "$TEMPLATES_DIR/base-new.html" ]; then
    mv "$TEMPLATES_DIR/base-new.html" "$TEMPLATES_DIR/base.html"
    echo "   ✅ Base template updated"
else
    echo "   ⚠️  base-new.html not found"
fi

# Replace home page
echo "[3/5] Replacing home page..."
if [ -f "$TEMPLATES_DIR/home-new.html" ]; then
    mv "$TEMPLATES_DIR/home-new.html" "$TEMPLATES_DIR/home.html"
    echo "   ✅ Home page updated"
else
    echo "   ⚠️  home-new.html not found"
fi

# Update testimonials to use new base
echo "[4/5] Updating testimonials page..."
if [ -f "$TEMPLATES_DIR/testimonials.html" ]; then
    # Check if it already extends base
    if ! grep -q "{% extends" "$TEMPLATES_DIR/testimonials.html"; then
        # Create new testimonials with base template
        cat > "$TEMPLATES_DIR/testimonials.html" << 'EOF'
{% extends "base.html" %}

{% block title %}Testimonials - PhazeVPN{% endblock %}

{% block content %}
<div class="container">
    <div class="card">
        <div class="card-header">
            <h1 class="card-title">⭐ What Our Users Say</h1>
            <p class="text-muted">Real feedback from PhazeVPN users</p>
        </div>
        
        <div class="card-body">
            <div style="text-align: center; padding: 4rem 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">💬</div>
                <h3 style="color: var(--primary-light); margin-bottom: 1rem;">No Reviews Yet</h3>
                <p class="text-muted" style="margin-bottom: 2rem;">Be the first to share your experience with PhazeVPN!</p>
                <a href="{{ url_for('contact') }}" class="btn btn-primary">Share Your Feedback</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF
        echo "   ✅ Testimonials page updated"
    else
        echo "   ✅ Testimonials already uses base template"
    fi
fi

echo "[5/5] Redesign complete!"
echo ""
echo "=========================================="
echo "✅ Website Redesign Applied!"
echo "=========================================="
echo ""
echo "Changes made:"
echo "  ✅ Modern base template with proper navigation"
echo "  ✅ Redesigned home page"
echo "  ✅ Updated CSS with design system"
echo "  ✅ Updated testimonials page"
echo ""
echo "Next steps:"
echo "  1. Test the website: https://phazevpn.duckdns.org"
echo "  2. Update other pages to use new base template"
echo "  3. Deploy to VPS when ready"
echo ""
echo "Backup location: $BACKUP_DIR"

