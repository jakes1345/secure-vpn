#!/usr/bin/env python3
"""
Update website to focus ONLY on PhazeVPN Protocol
- Remove OpenVPN desktop tutorials
- Add PhazeBrowser mentions
- Make mobile VPN (OpenVPN/WireGuard) temporary
"""

from pathlib import Path
import re

print("=" * 80)
print("🌐 UPDATING WEBSITE - PHAZEVPN PROTOCOL ONLY")
print("=" * 80)
print("")

# 1. Update guide.html
print("1️⃣ Updating guide.html...")
guide_file = Path("web-portal/templates/guide.html")

if guide_file.exists():
    # Backup old file
    backup = Path(f"web-portal/templates/guide-backup-{Path(guide_file).stat().st_mtime}.html")
    if not backup.exists():
        guide_file.rename(backup)
        print("   ✅ Backed up old guide.html")
    
    # Use new guide
    new_guide = Path("web-portal/templates/guide-new.html")
    if new_guide.exists():
        new_guide.rename(guide_file)
        print("   ✅ Updated guide.html")
    else:
        print("   ⚠️  guide-new.html not found, creating from template...")
        # Create new guide content
        guide_content = '''{% extends "base.html" %}

{% block title %}PhazeVPN Setup Guide{% endblock %}

{% block content %}
<h1>📖 PhazeVPN Protocol Setup Guide</h1>
<p>Get started with PhazeVPN Protocol - The most secure VPN with built-in browsing!</p>

<!-- Desktop: PhazeVPN Protocol -->
<div class="card" style="margin-top: 2rem;">
    <div class="card-header">
        <h2>🔒 Desktop VPN - PhazeVPN Protocol (Main)</h2>
    </div>
    <div class="card-body">
        <p><strong>PhazeVPN Protocol</strong> is our main VPN with:</p>
        <ul>
            <li>✅ Zero-knowledge architecture</li>
            <li>✅ Built-in PhazeBrowser</li>
            <li>✅ Patent-pending security</li>
            <li>✅ VPN modes (Normal, Semi Ghost, Full Ghost)</li>
        </ul>
        <p><a href="/download" class="btn btn-primary">Download PhazeVPN Client</a></p>
    </div>
</div>

<!-- Mobile: Temporary -->
<div class="card" style="margin-top: 2rem;">
    <div class="card-header">
        <h2>📱 Mobile VPN (Temporary)</h2>
    </div>
    <div class="card-body">
        <p>Use OpenVPN or WireGuard apps temporarily until PhazeVPN mobile app is ready.</p>
        <p>See mobile setup instructions below.</p>
    </div>
</div>

<!-- Tutorial videos placeholder -->
<div class="card" style="margin-top: 2rem;">
    <div class="card-header">🎥 Video Tutorials</div>
    <div class="card-body">
        <p>Video tutorials coming soon! For now, follow the written guides.</p>
    </div>
</div>
{% endblock %}
'''
        guide_file.write_text(guide_content)
        print("   ✅ Created new guide.html")
else:
    print("   ⚠️  guide.html not found")

print("")

# 2. Update home.html to mention PhazeBrowser
print("2️⃣ Updating home.html...")
home_file = Path("web-portal/templates/home.html")

if home_file.exists():
    content = home_file.read_text()
    
    # Add PhazeBrowser feature if not present
    if "PhazeBrowser" not in content:
        # Find features grid and add browser feature
        browser_feature = '''
        <div class="card">
            <div class="card-header">
                <h3 style="font-size: 2rem; margin-bottom: 0.5rem;">🌐</h3>
                <h3 class="card-title">Built-in Secure Browser</h3>
            </div>
            <div class="card-body">
                <p>PhazeBrowser - VPN-native browser with built-in security. No extensions needed.</p>
            </div>
        </div>
'''
        # Insert before closing grid
        if '<div class="grid grid-3"' in content:
            content = content.replace(
                '</div>\n    </div>\n\n    <!-- Why Choose',
                browser_feature + '\n    </div>\n\n    <!-- Why Choose'
            )
            home_file.write_text(content)
            print("   ✅ Added PhazeBrowser to home page")
    
    # Update main hero text
    if "Military-grade encryption" in content:
        content = content.replace(
            "Military-grade encryption, zero-logs policy, and network-level security.",
            "PhazeVPN Protocol - Patent-pending security with built-in PhazeBrowser. Zero-knowledge architecture, RAM-only operations."
        )
        home_file.write_text(content)
        print("   ✅ Updated hero text")
else:
    print("   ⚠️  home.html not found")

print("")

# 3. Update download.html to focus on PhazeVPN Protocol
print("3️⃣ Updating download.html...")
download_file = Path("web-portal/templates/download.html")

if download_file.exists():
    content = download_file.read_text()
    
    # Update header
    if "Download PhazeVPN Client" in content:
        content = content.replace(
            "Get the official PhazeVPN desktop client for your computer",
            "Download PhazeVPN Protocol client with built-in PhazeBrowser - The most secure VPN"
        )
        download_file.write_text(content)
        print("   ✅ Updated download page header")
else:
    print("   ⚠️  download.html not found")

print("")

# 4. Create PhazeBrowser info page
print("4️⃣ Creating PhazeBrowser info page...")
browser_info = Path("web-portal/templates/phazebrowser.html")

browser_content = '''{% extends "base.html" %}

{% block title %}PhazeBrowser - Built-in Secure Browser{% endblock %}

{% block content %}
<div class="container">
    <h1>🌐 PhazeBrowser - Built-in Secure Browser</h1>
    <p>PhazeBrowser is built into PhazeVPN Protocol - a custom browser with VPN-native security!</p>
    
    <div class="card" style="margin-top: 2rem;">
        <div class="card-header">
            <h2>✨ Features</h2>
        </div>
        <div class="card-body">
            <ul style="line-height: 2.5;">
                <li>✅ <strong>VPN-Native Security</strong> - All traffic through VPN, WebRTC/IPv6 routing</li>
                <li>✅ <strong>Built-in Ad Blocking</strong> - No extensions needed</li>
                <li>✅ <strong>Tracking Protection</strong> - Blocks trackers automatically</li>
                <li>✅ <strong>Fingerprinting Protection</strong> - Prevents browser fingerprinting</li>
                <li>✅ <strong>Kill Switch</strong> - Browser won't work without VPN</li>
                <li>✅ <strong>DNS Leak Protection</strong> - All DNS through VPN</li>
            </ul>
        </div>
    </div>
    
    <div class="card" style="margin-top: 2rem;">
        <div class="card-header">
            <h2>🚀 How It Works</h2>
        </div>
        <div class="card-body">
            <ol style="line-height: 2.5;">
                <li>Connect to PhazeVPN Protocol</li>
                <li>Launch PhazeBrowser (built into the client)</li>
                <li>Browse securely - all traffic through VPN</li>
                <li>No browser extensions needed - security is built-in!</li>
            </ol>
        </div>
    </div>
    
    <div class="card" style="margin-top: 2rem;">
        <div class="card-header">
            <h2>📋 Availability</h2>
        </div>
        <div class="card-body">
            <p>PhazeBrowser comes with PhazeVPN Protocol client:</p>
            <ul style="line-height: 2;">
                <li>✅ Windows - Included in PhazeVPN client</li>
                <li>✅ Linux - Included in PhazeVPN client</li>
                <li>✅ macOS - Included in PhazeVPN client</li>
                <li>⏳ Mobile - Coming soon with PhazeVPN mobile app</li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}
'''
browser_info.write_text(browser_content)
print("   ✅ Created phazebrowser.html")

print("")

# 5. Update app.py routes
print("5️⃣ Updating app.py routes...")
app_file = Path("web-portal/app.py")

if app_file.exists():
    content = app_file.read_text()
    
    # Add PhazeBrowser route if not exists
    if "@app.route('/phazebrowser')" not in content:
        browser_route = '''
@app.route('/phazebrowser')
def phazebrowser_info():
    """PhazeBrowser information page"""
    return render_template('phazebrowser.html')
'''
        # Add before guide route
        if "@app.route('/guide')" in content:
            content = content.replace(
                "@app.route('/guide')",
                browser_route + "\n@app.route('/guide')"
            )
            app_file.write_text(content)
            print("   ✅ Added PhazeBrowser route")
    
    # Update guide route description
    if "def guide():" in content:
        content = content.replace(
            '"""VPN Setup Guide"""',
            '"""PhazeVPN Protocol Setup Guide - Desktop VPN"""'
        )
        app_file.write_text(content)
        print("   ✅ Updated guide route")

print("")

print("=" * 80)
print("✅ WEBSITE UPDATED!")
print("=" * 80)
print("")
print("📋 Changes:")
print("   ✅ Guide updated - PhazeVPN Protocol focus")
print("   ✅ Home page - PhazeBrowser mention")
print("   ✅ Download page - PhazeVPN Protocol focus")
print("   ✅ Mobile VPN - Marked as temporary")
print("   ✅ Video tutorials - Placeholder added")
print("   ✅ PhazeBrowser info page created")
print("")

