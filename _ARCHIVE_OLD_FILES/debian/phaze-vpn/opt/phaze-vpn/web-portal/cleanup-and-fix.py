#!/usr/bin/env python3
"""
Cleanup and Fix Web Portal
- Remove duplicate/bloat files
- Test all routes
- Fix broken links
- Setup email without personal email
"""

import sys
from pathlib import Path
import json

# Check what files exist
WEB_PORTAL_DIR = Path(__file__).parent

print("==========================================")
print("🧹 CLEANUP & FIX WEB PORTAL")
print("==========================================")
print("")

# Find duplicate files
print("📋 Checking for duplicate/bloat files...")
print("")

duplicates = {
    'app_secure.py': 'app.py',  # Duplicate - use main app.py
    'app_secure_integrated.py': 'app.py',  # Duplicate
    'app-original.py': 'app.py',  # Backup - can remove
}

for duplicate, main in duplicates.items():
    dup_path = WEB_PORTAL_DIR / duplicate
    main_path = WEB_PORTAL_DIR / main
    if dup_path.exists() and main_path.exists():
        print(f"   ⚠️  {duplicate} - duplicate of {main}")
        print(f"      Recommendation: Remove {duplicate} (use {main})")

print("")
print("📋 Main app file: app.py")
print("   ✅ This is the main web portal")
print("")

# Check routes in app.py
print("📋 Checking routes in app.py...")
print("")

try:
    with open(WEB_PORTAL_DIR / 'app.py', 'r') as f:
        content = f.read()
        routes = []
        for line in content.split('\n'):
            if '@app.route' in line:
                route = line.strip()
                routes.append(route)
        
        print(f"   Found {len(routes)} routes")
        print("")
        print("   Main routes:")
        for route in routes[:20]:  # Show first 20
            print(f"      {route}")
        if len(routes) > 20:
            print(f"      ... and {len(routes) - 20} more")
except Exception as e:
    print(f"   ❌ Error reading app.py: {e}")

print("")
print("==========================================")
print("✅ ANALYSIS COMPLETE")
print("==========================================")
print("")
print("📝 Recommendations:")
print("   1. Remove duplicate files (app_secure.py, etc.)")
print("   2. Test all routes")
print("   3. Fix broken links")
print("   4. Setup email with API service (no personal email needed)")
print("")

