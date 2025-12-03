#!/usr/bin/env python3
"""
Comprehensive audit of 0.0.0.0 usage in codebase
Finds and categorizes all instances to ensure correct usage
"""

import os
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/media/jack/Liunux/secure-vpn")

# Patterns that are CORRECT (server binding)
CORRECT_PATTERNS = [
    r'app\.run\(host=[\'"]0\.0\.0\.0',
    r'HTTPServer\(\([\'"]0\.0\.0\.0',
    r'bind\(\([\'"]0\.0\.0\.0',
    r'-host\s+0\.0\.0\.0',
    r'host.*=.*[\'"]0\.0\.0\.0[\'"].*port',  # Server binding
    r'ExecStart.*-host\s+0\.0\.0\.0',  # Systemd service
    r'gunicorn.*-b\s+0\.0\.0\.0',  # Gunicorn binding
    r'hosts\s*=\s*0\.0\.0\.0',  # Email server binding
]

# Patterns that are WRONG (client configs)
WRONG_PATTERNS = [
    r'Server\s*=\s*0\.0\.0\.0',
    r'server\s*=\s*0\.0\.0\.0',  # In client configs
    r'remote\s+0\.0\.0\.0',
    r'connect.*0\.0\.0\.0',
    r'server_ip.*=.*0\.0\.0\.0',
    r'server_host.*=.*0\.0\.0\.0',
    r'ServerHost.*=.*0\.0\.0\.0',
]

# Files to skip (logs, build artifacts, etc.)
SKIP_PATTERNS = [
    r'\.log$',
    r'\.pyc$',
    r'__pycache__',
    r'\.git',
    r'node_modules',
    r'\.deb$',
    r'\.spec$',
    r'build/',
    r'dist/',
]

def should_skip_file(filepath):
    """Check if file should be skipped"""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, str(filepath)):
            return True
    return False

def find_all_occurrences():
    """Find all 0.0.0.0 occurrences and categorize them"""
    results = {
        'correct': [],  # Server bindings (OK)
        'wrong': [],    # Client configs (BAD)
        'unknown': [],  # Need manual review
    }
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip certain directories
        dirs[:] = [d for d in dirs if not should_skip_file(Path(root) / d)]
        
        for file in files:
            filepath = Path(root) / file
            
            if should_skip_file(filepath):
                continue
            
            try:
                # Skip binary files
                if filepath.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz']:
                    continue
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        if '0.0.0.0' in line:
                            # Check if it's a correct pattern
                            is_correct = False
                            is_wrong = False
                            
                            for pattern in CORRECT_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    is_correct = True
                                    break
                            
                            for pattern in WRONG_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    is_wrong = True
                                    break
                            
                            rel_path = filepath.relative_to(BASE_DIR)
                            entry = {
                                'file': str(rel_path),
                                'line': line_num,
                                'content': line.strip()[:100]
                            }
                            
                            if is_correct:
                                results['correct'].append(entry)
                            elif is_wrong:
                                results['wrong'].append(entry)
                            else:
                                results['unknown'].append(entry)
            except Exception as e:
                # Skip files we can't read
                continue
    
    return results

def main():
    print("=" * 70)
    print("🔍 Comprehensive 0.0.0.0 Usage Audit")
    print("=" * 70)
    print()
    print("Scanning entire codebase...")
    print()
    
    results = find_all_occurrences()
    
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    print()
    
    # Show WRONG first (most important)
    if results['wrong']:
        print(f"❌ WRONG USAGE ({len(results['wrong'])} found):")
        print("   These are in CLIENT configs and need to be fixed!")
        print()
        for entry in results['wrong']:
            print(f"   {entry['file']}:{entry['line']}")
            print(f"      {entry['content']}")
            print()
    else:
        print("✅ No wrong usage found!")
        print()
    
    # Show UNKNOWN (need review)
    if results['unknown']:
        print(f"⚠️  UNKNOWN ({len(results['unknown'])} found - need manual review):")
        print()
        for entry in results['unknown'][:20]:  # Show first 20
            print(f"   {entry['file']}:{entry['line']}")
            print(f"      {entry['content']}")
            print()
        if len(results['unknown']) > 20:
            print(f"   ... and {len(results['unknown']) - 20} more")
            print()
    
    # Show CORRECT (for reference)
    print(f"✅ CORRECT USAGE ({len(results['correct'])} found):")
    print("   These are server bindings (listening on all interfaces) - OK!")
    print()
    
    # Summary
    print("=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print(f"   ✅ Correct (server bindings): {len(results['correct'])}")
    print(f"   ❌ Wrong (client configs): {len(results['wrong'])}")
    print(f"   ⚠️  Unknown (needs review): {len(results['unknown'])}")
    print()
    
    if results['wrong']:
        print("⚠️  ACTION REQUIRED:")
        print("   Fix the wrong usages above - clients cannot connect to 0.0.0.0!")
        print("   They need the actual server IP or domain (phazevpn.com)")
        print()
    else:
        print("✅ All client configs look good!")
        print()

if __name__ == "__main__":
    main()

