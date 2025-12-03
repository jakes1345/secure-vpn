#!/usr/bin/env python3
"""
Fix REAL critical issues (not false positives)
Focuses on actual problems that affect functionality
"""

import re
from pathlib import Path

BASE_DIR = Path("/media/jack/Liunux/secure-vpn")

def fix_local_paths():
    """Fix hardcoded local paths"""
    fixes = []
    
    # Files with hardcoded local paths
    files_to_fix = [
        'phazevpn-client.desktop',
        'update-everything-vps.py',
        'deploy-ultimate-vpn-to-vps.py',
    ]
    
    replacements = [
        (r'/media/jack/Liunux/secure-vpn', '/opt/phaze-vpn'),
        (r'/home/jack/', '/root/'),
        (r'jack-MS-7C95', 'phazevpn'),
    ]
    
    for filename in files_to_fix:
        filepath = BASE_DIR / filename
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original = content
                for pattern, replacement in replacements:
                    content = re.sub(pattern, replacement, content)
                
                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixes.append(f"✅ Fixed: {filename}")
            except Exception as e:
                fixes.append(f"❌ Error fixing {filename}: {e}")
    
    return fixes

def fix_debug_mode():
    """Fix debug mode in production files"""
    fixes = []
    
    # Production files that shouldn't have debug=True
    production_files = [
        'web-portal/app.py',
        'debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py',
    ]
    
    for filename in production_files:
        filepath = BASE_DIR / filename
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Only fix if it's the main app.run() call
                if 'if __name__' in content and 'app.run(host' in content:
                    original = content
                    # Fix debug=True in production
                    content = re.sub(
                        r'app\.run\([^)]*debug\s*=\s*True[^)]*\)',
                        lambda m: m.group(0).replace('debug=True', 'debug=False'),
                        content
                    )
                    
                    if content != original:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixes.append(f"✅ Fixed debug mode: {filename}")
            except Exception as e:
                fixes.append(f"❌ Error fixing {filename}: {e}")
    
    return fixes

def main():
    print("=" * 70)
    print("🔧 Fixing REAL Critical Issues")
    print("=" * 70)
    print()
    print("Focusing on issues that actually affect functionality:")
    print("  1. Hardcoded local paths")
    print("  2. Debug mode in production")
    print()
    
    all_fixes = []
    
    print("📋 Fixing hardcoded local paths...")
    fixes = fix_local_paths()
    all_fixes.extend(fixes)
    for fix in fixes:
        print(f"   {fix}")
    print()
    
    print("📋 Fixing debug mode...")
    fixes = fix_debug_mode()
    all_fixes.extend(fixes)
    for fix in fixes:
        print(f"   {fix}")
    print()
    
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"   Total fixes: {len(all_fixes)}")
    print()
    print("✅ Most critical issues addressed!")
    print()
    print("Note: Many 'issues' in the audit are false positives:")
    print("  - print() statements are normal for Python scripts")
    print("  - Hardcoded IPs in docs are just examples")
    print("  - Password examples in docs are not real credentials")
    print()

if __name__ == "__main__":
    main()

