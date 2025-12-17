#!/usr/bin/env python3
"""
Fix critical issues found in codebase audit
Focuses on HIGH and CRITICAL severity issues
"""

import re
from pathlib import Path

BASE_DIR = Path("/media/jack/Liunux/secure-vpn")

# Files to fix
FIXES = [
    {
        'file': 'phazevpn-client.desktop',
        'pattern': r'/media/jack/Liunux/secure-vpn',
        'replacement': '/opt/phaze-vpn',
        'description': 'Fix hardcoded local path in desktop file'
    },
    {
        'file': 'update-everything-vps.py',
        'pattern': r'/media/jack/Liunux/secure-vpn',
        'replacement': '/opt/phaze-vpn',
        'description': 'Fix hardcoded local path in deployment script'
    },
    {
        'file': 'deploy-ultimate-vpn-to-vps.py',
        'pattern': r'/media/jack/Liunux/secure-vpn',
        'replacement': '/opt/phaze-vpn',
        'description': 'Fix hardcoded local path in deployment script'
    },
]

def fix_file(filepath, pattern, replacement):
    """Fix a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        content = re.sub(pattern, replacement, content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Fixed"
        else:
            return False, "No changes needed"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    print("=" * 70)
    print("🔧 Fixing Critical Issues")
    print("=" * 70)
    print()
    
    fixed_count = 0
    error_count = 0
    
    for fix_config in FIXES:
        filepath = BASE_DIR / fix_config['file']
        
        if not filepath.exists():
            print(f"⚠️  {fix_config['file']}: Not found (skipping)")
            continue
        
        print(f"📝 Fixing: {fix_config['file']}")
        print(f"   {fix_config['description']}")
        
        success, message = fix_file(
            filepath,
            fix_config['pattern'],
            fix_config['replacement']
        )
        
        if success:
            print(f"   ✅ {message}")
            fixed_count += 1
        else:
            print(f"   {message}")
            if "Error" in message:
                error_count += 1
        print()
    
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ⚠️  Errors: {error_count}")
    print()
    print("Note: This fixes the most critical issues.")
    print("Run the audit again to see remaining issues.")
    print()

if __name__ == "__main__":
    main()

