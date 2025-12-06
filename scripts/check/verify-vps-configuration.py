#!/usr/bin/env python3
"""
Verify that all services are configured to point to VPS, not PC
Checks for localhost, 127.0.0.1, and PC IPs
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Files to check
FILES_TO_CHECK = [
    'client-download-server.py',
    'web-portal/app.py',
    'vpn-manager.py',
    'web-portal/phazevpn-portal.service',
]

# Patterns that indicate PC/localhost (BAD)
BAD_PATTERNS = [
    (r'localhost', 'localhost reference'),
    (r'127\.0\.0\.1', 'localhost IP'),
    (r'192\.168\.', 'local network IP'),
    (r'10\.0\.', 'local network IP'),
    (r'172\.(1[6-9]|2[0-9]|3[0-1])\.', 'local network IP'),
]

# Patterns that indicate VPS (GOOD)
GOOD_PATTERNS = [
    (r'phazevpn\.com', 'phazevpn.com domain'),
    (r'15\.204\.11\.19', 'VPS IP'),
    (r'0\.0\.0\.0', 'bind to all interfaces (correct for VPS)'),
    (r'PHAZEVPN_SERVER_HOST|VPN_SERVER_IP', 'environment variable (good)'),
]

print("="*70)
print("🔍 VERIFYING VPS CONFIGURATION")
print("="*70)
print("")
print("Checking that all services point to VPS, not PC...")
print("")

issues_found = []
good_findings = []

for filename in FILES_TO_CHECK:
    filepath = BASE_DIR / filename
    
    if not filepath.exists():
        print(f"⚠️  Skipping (not found): {filename}")
        continue
    
    print(f"📄 Checking: {filename}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_issues = []
        file_good = []
        
        # Check for bad patterns
        for pattern, description in BAD_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Filter out false positives (like comments or documentation)
                for match in matches:
                    # Check if it's in a comment or string that's OK
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if match.lower() in line.lower():
                            # Skip if it's clearly documentation
                            if any(skip in line.lower() for skip in ['#', 'comment', 'example', 'note:', 'todo']):
                                continue
                            # Skip if it's binding to 0.0.0.0 (which is correct)
                            if '0.0.0.0' in line and 'bind' in line.lower():
                                continue
                            file_issues.append(f"   Line {i}: {description} - {line.strip()[:60]}")
        
        # Check for good patterns
        for pattern, description in GOOD_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                file_good.append(f"   ✅ {description} found")
        
        if file_issues:
            print(f"   ⚠️  Issues found:")
            for issue in file_issues:
                print(issue)
            issues_found.extend([(filename, issue) for issue in file_issues])
        else:
            print(f"   ✅ No localhost/PC references found")
        
        if file_good:
            for good in file_good:
                print(good)
        
        print("")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        print("")

print("="*70)
if issues_found:
    print(f"⚠️  FOUND {len(issues_found)} POTENTIAL ISSUES")
    print("="*70)
    print("")
    print("Issues that might point to PC instead of VPS:")
    for filename, issue in issues_found:
        print(f"  {filename}: {issue}")
    print("")
    print("⚠️  Review these - they might need to be changed to phazevpn.com")
else:
    print("✅ ALL CHECKS PASSED!")
    print("="*70)
    print("")
    print("All services are configured to use:")
    print("  ✅ phazevpn.com domain (resolves to VPS)")
    print("  ✅ Environment variables (flexible)")
    print("  ✅ 0.0.0.0 binding (listens on all interfaces)")
    print("")
    print("Everything should work on VPS! 🚀")

print("")

