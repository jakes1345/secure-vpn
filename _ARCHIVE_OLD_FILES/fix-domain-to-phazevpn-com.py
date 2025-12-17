#!/usr/bin/env python3
"""
Fix all domain references from duckdns.org to phazevpn.com
Updates all key files that get deployed
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Files to update (key deployment files)
FILES_TO_FIX = [
    'deploy-everything-to-vps.py',
    'client-download-server.py',
    'vpn-manager.py',
    'web-portal/app.py',
    'create-update-notification.py',
    'multi-ip-manager.py',
    'mobile-config-generator.py',
]

print("="*70)
print("🔧 FIXING DOMAIN REFERENCES: duckdns.org → phazevpn.com")
print("="*70)
print("")

fixed_count = 0
total_replacements = 0

for filename in FILES_TO_FIX:
    filepath = BASE_DIR / filename
    
    if not filepath.exists():
        print(f"⚠️  Skipping (not found): {filename}")
        continue
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace all variations
        replacements = [
            (r'phazevpn\.duckdns\.org', 'phazevpn.com'),
            (r'phazevpn\.duckdns', 'phazevpn.com'),
            (r'duckdns\.org', 'phazevpn.com'),
        ]
        
        for pattern, replacement in replacements:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            if matches > 0:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                total_replacements += matches
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {filename} ({total_replacements} replacements)")
            fixed_count += 1
        else:
            print(f"✓ Already correct: {filename}")
    except Exception as e:
        print(f"❌ Error fixing {filename}: {e}")

print("")
print("="*70)
print(f"✅ FIXED {fixed_count} FILES")
print(f"   Total replacements: {total_replacements}")
print("="*70)
print("")
print("All domain references updated to phazevpn.com!")
print("")

