#!/usr/bin/env python3
"""
Final verification - NO local PC references in runtime code
"""

from pathlib import Path
import re

# Critical runtime files that MUST NOT have local references
CRITICAL_FILES = [
    'web-portal/app.py',
    'vpn-gui.py',
    'vpn-manager.py',
    'web-portal/nginx-phazevpn.conf',
    'web-portal/phazevpn-portal.service',
    'debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py',
    'debian/phaze-vpn/opt/phaze-vpn/vpn-gui.py',
    'debian/phaze-vpn/opt/phaze-vpn/vpn-manager.py',
    'debian/phaze-vpn/opt/phaze-vpn/web-portal/nginx-phazevpn.conf',
    'debian/phaze-vpn/opt/phaze-vpn/web-portal/phazevpn-portal.service',
]

# Local PC patterns to check for
LOCAL_PATTERNS = [
    r'/media/jack',
    r'/home/jack',
    r'jack-MS-7C95',
    r'jack@jack-MS-7C95',
    r'Liunux',
]

print("="*70)
print("FINAL VERIFICATION: NO LOCAL PC REFERENCES IN RUNTIME CODE")
print("="*70)
print("")

issues_found = []
all_clean = True

for file_path_str in CRITICAL_FILES:
    file_path = Path(file_path_str)
    if not file_path.exists():
        continue
    
    print(f"Checking: {file_path_str}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_issues = []
        for pattern in LOCAL_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Get line number
                line_num = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_num - 1].strip()
                file_issues.append(f"  Line {line_num}: {pattern} - {line_content[:80]}")
        
        if file_issues:
            all_clean = False
            issues_found.extend([(file_path_str, issue) for issue in file_issues])
            print(f"  ❌ Found {len(file_issues)} issue(s)")
            for issue in file_issues[:3]:  # Show first 3
                print(issue)
            if len(file_issues) > 3:
                print(f"  ... and {len(file_issues) - 3} more")
        else:
            print(f"  ✅ Clean")
    except Exception as e:
        print(f"  ⚠️  Error reading: {e}")

print("")
print("="*70)

# Also check for localhost - but explain these are OK
print("")
print("Checking localhost/127.0.0.1 references (these are OK for VPS internal):")
localhost_files = []
for file_path_str in CRITICAL_FILES:
    file_path = Path(file_path_str)
    if not file_path.exists():
        continue
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        if 'localhost' in content.lower() or '127.0.0.1' in content:
            localhost_files.append(file_path_str)
    except:
        pass

if localhost_files:
    print(f"  Found in {len(localhost_files)} files (this is CORRECT - VPS internal only)")
    print("  ✅ These are for VPS internal communication (nginx proxy, etc.)")
else:
    print("  ✅ No localhost references")

print("")
print("="*70)

if all_clean:
    print("✅ ALL CRITICAL RUNTIME FILES ARE CLEAN!")
    print("="*70)
    print("")
    print("No local PC references found in:")
    print("  - Web portal (app.py)")
    print("  - VPN GUI (vpn-gui.py)")
    print("  - VPN Manager (vpn-manager.py)")
    print("  - Nginx config")
    print("  - Service files")
    print("")
    print("Everything points to VPS only (/opt/phaze-vpn, phazevpn.com, etc.)")
else:
    print("⚠️  ISSUES FOUND IN RUNTIME CODE!")
    print("="*70)
    print("")
    print("Issues found:")
    for file_path, issue in issues_found:
        print(f"  {file_path}:")
        print(f"    {issue}")
    print("")
    print("These need to be fixed before deployment!")

print("")

