#!/usr/bin/env python3
"""
Test all web portal routes to find broken links
"""

import sys
from pathlib import Path
import re

WEB_PORTAL_DIR = Path(__file__).parent
APP_FILE = WEB_PORTAL_DIR / 'app.py'

print("==========================================")
print("🔍 TESTING WEB PORTAL ROUTES")
print("==========================================")
print("")

if not APP_FILE.exists():
    print(f"❌ {APP_FILE} not found!")
    sys.exit(1)

# Read app.py
with open(APP_FILE, 'r') as f:
    content = f.read()

# Find all routes
routes = []
route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"]"
for match in re.finditer(route_pattern, content):
    route = match.group(1)
    routes.append(route)

# Find all url_for calls (internal links)
url_for_pattern = r"url_for\(['\"]([^'\"]+)['\"]"
url_for_calls = []
for match in re.finditer(url_for_pattern, content):
    url = match.group(1)
    url_for_calls.append(url)

# Find all redirect calls
redirect_pattern = r"redirect\(url_for\(['\"]([^'\"]+)['\"]"
redirects = []
for match in re.finditer(redirect_pattern, content):
    url = match.group(1)
    redirects.append(url)

print(f"📊 Found {len(routes)} routes")
print("")
print("Routes:")
for route in sorted(set(routes)):
    print(f"   ✅ {route}")

print("")
print(f"📊 Found {len(url_for_calls)} url_for calls")
print("")
print("Internal links:")
for url in sorted(set(url_for_calls)):
    # Check if route exists
    if url in routes or f'/{url}' in routes:
        print(f"   ✅ {url}")
    else:
        print(f"   ❌ {url} - ROUTE NOT FOUND!")

print("")
print("==========================================")
print("✅ ROUTE CHECK COMPLETE")
print("==========================================")
print("")
print("📝 Next: Fix broken routes and remove bloat")
print("")

