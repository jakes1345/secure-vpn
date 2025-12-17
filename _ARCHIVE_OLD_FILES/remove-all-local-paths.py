#!/usr/bin/env python3
"""
Remove ALL local PC paths and references from codebase
Ensures everything points to VPS only
"""

import re
from pathlib import Path

# Local paths to find and replace
LOCAL_PATHS = [
    r'/opt/phaze-vpn',
    r'/root',
    r'phazevpn
    r'jack@phazevpn
]

# VPS paths to use instead
VPS_BASE = '/opt/phaze-vpn'

def fix_file(file_path):
    """Fix a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Replace local paths
        for local_path in LOCAL_PATHS:
            if local_path in content:
                # Replace with VPS path
                if 'secure-vpn' in local_path:
                    new_path = content.replace(local_path, VPS_BASE)
                    if new_path != content:
                        content = new_path
                        changes.append(f"Replaced {local_path} with {VPS_BASE}")
                elif 'phazevpn in local_path or 'jack@phazevpn in local_path:
                    # Remove these references or replace with VPS hostname
                    content = re.sub(r'phazevpn 'phazevpn', content)
                    content = re.sub(r'jack@phazevpn 'root@phazevpn', content)
                    changes.append(f"Replaced {local_path} references")
                elif '/root' in local_path:
                    # Replace with /root or /opt/phaze-vpn
                    content = content.replace('/root', '/root')
                    changes.append(f"Replaced /root with /root")
        
        # Fix nginx config specifically
        if 'nginx' in str(file_path).lower() or 'nginx-phazevpn.conf' in str(file_path):
            # Fix static file alias
            content = re.sub(
                r'alias\s+/opt/phaze-vpn/web-portal/static',
                f'alias {VPS_BASE}/web-portal/static',
                content
            )
            if 'alias /media/jack' in content:
                changes.append("Fixed nginx static alias")
        
        # Fix service files
        if '.service' in str(file_path):
            # Fix WorkingDirectory
            content = re.sub(
                r'WorkingDirectory=/opt/phaze-vpn[^\s]*',
                f'WorkingDirectory={VPS_BASE}',
                content
            )
            # Fix ExecStart paths
            content = re.sub(
                r'ExecStart=[^\s]*/opt/phaze-vpn[^\s]*',
                lambda m: m.group(0).replace('/opt/phaze-vpn', VPS_BASE),
                content
            )
            if '/media/jack' in content:
                changes.append("Fixed service file paths")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes
        return []
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return []

def main():
    print("="*70)
    print("REMOVING ALL LOCAL PC PATHS FROM CODEBASE")
    print("="*70)
    print("")
    
    base_dir = Path('.')
    files_fixed = 0
    total_changes = []
    
    # Files to check (Python, shell scripts, config files, service files)
    patterns = [
        '**/*.py',
        '**/*.sh',
        '**/*.conf',
        '**/*.service',
        '**/*.json',
        '**/*.md',
    ]
    
    all_files = []
    for pattern in patterns:
        all_files.extend(base_dir.glob(pattern))
    
    # Also check specific important files
    important_files = [
        'debian/phaze-vpn/opt/phaze-vpn/web-portal/nginx-phazevpn.conf',
        'debian/phaze-vpn/opt/phaze-vpn/web-portal/phazevpn-portal.service',
    ]
    
    for imp_file in important_files:
        if Path(imp_file).exists() and Path(imp_file) not in all_files:
            all_files.append(Path(imp_file))
    
    print(f"Scanning {len(all_files)} files...")
    print("")
    
    for file_path in all_files:
        # Skip certain directories
        if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'node_modules', 'dist', 'build']):
            continue
        
        changes = fix_file(file_path)
        if changes:
            files_fixed += 1
            print(f"✅ Fixed: {file_path}")
            for change in changes:
                print(f"   - {change}")
                total_changes.append(f"{file_path}: {change}")
    
    print("")
    print("="*70)
    print(f"✅ FIXED {files_fixed} FILES")
    print("="*70)
    print("")
    print("Summary of changes:")
    for change in total_changes[:20]:  # Show first 20
        print(f"  - {change}")
    if len(total_changes) > 20:
        print(f"  ... and {len(total_changes) - 20} more changes")
    print("")
    print("All local PC paths have been replaced with VPS paths.")
    print("")

if __name__ == '__main__':
    main()

