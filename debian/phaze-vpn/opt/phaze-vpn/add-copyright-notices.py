#!/usr/bin/env python3
"""
Add copyright notices to all code files
Protects your IP immediately
"""

from pathlib import Path
import re
from datetime import datetime

# Copyright notice to add
COPYRIGHT_NOTICE = """Copyright (c) 2024 PhazeVPN. All Rights Reserved.
Proprietary and Confidential. Unauthorized copying, modification,
distribution, or use of this software is strictly prohibited."""

COPYRIGHT_COMMENT_PATTERNS = {
    '.py': '#',
    '.js': '//',
    '.ts': '//',
    '.cpp': '//',
    '.cc': '//',
    '.h': '//',
    '.hpp': '//',
    '.html': '<!--',
    '.css': '/*',
    '.sh': '#',
    '.yaml': '#',
    '.yml': '#',
    '.json': '//',
}

def get_comment_prefix(file_path):
    """Get comment prefix for file type"""
    suffix = file_path.suffix.lower()
    if suffix in COPYRIGHT_COMMENT_PATTERNS:
        return COPYRIGHT_COMMENT_PATTERNS[suffix]
    return '#'  # Default to #

def format_copyright(file_path):
    """Format copyright notice for file type"""
    prefix = get_comment_prefix(file_path)
    suffix = file_path.suffix.lower()
    
    if suffix in ['.html']:
        return f"""<!--
{COPYRIGHT_NOTICE}
-->"""
    elif suffix in ['.css']:
        return f"""/*
{COPYRIGHT_NOTICE}
*/"""
    else:
        # Regular comment style
        lines = COPYRIGHT_NOTICE.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip():
                formatted_lines.append(f"{prefix} {line}")
            else:
                formatted_lines.append(prefix)
        return '\n'.join(formatted_lines)

def has_copyright(file_content):
    """Check if file already has copyright notice"""
    copyright_keywords = ['Copyright', 'copyright', 'Proprietary', 'All Rights Reserved']
    return any(keyword in file_content[:500] for keyword in copyright_keywords)

def add_copyright_to_file(file_path):
    """Add copyright to a single file"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Skip if already has copyright
        if has_copyright(content):
            return False, "Already has copyright"
        
        # Generate copyright notice
        copyright_notice = format_copyright(file_path)
        
        # Skip binary files or very large files
        if len(content) > 1000000:  # 1MB
            return False, "File too large"
        
        # Add copyright notice
        if file_path.suffix.lower() in ['.html']:
            # For HTML, add after <!DOCTYPE> or <html>
            if content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html'):
                # Find end of opening tag
                first_line_end = content.find('\n', content.find('>'))
                if first_line_end > 0:
                    new_content = content[:first_line_end+1] + '\n' + copyright_notice + '\n' + content[first_line_end+1:]
                else:
                    new_content = copyright_notice + '\n\n' + content
            else:
                new_content = copyright_notice + '\n\n' + content
        else:
            # For code files, add at the very top
            # Skip shebang line if present
            if content.startswith('#!'):
                shebang_end = content.find('\n')
                if shebang_end > 0:
                    new_content = content[:shebang_end+1] + copyright_notice + '\n\n' + content[shebang_end+1:]
                else:
                    new_content = content + '\n\n' + copyright_notice
            else:
                new_content = copyright_notice + '\n\n' + content
        
        # Write back
        file_path.write_text(new_content, encoding='utf-8')
        return True, "Copyright added"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print("=" * 80)
    print("🔒 ADDING COPYRIGHT NOTICES TO ALL CODE FILES")
    print("=" * 80)
    print("")
    
    base_dir = Path(__file__).parent
    
    # File extensions to process
    extensions = ['.py', '.js', '.ts', '.cpp', '.cc', '.h', '.hpp', '.html', '.css', '.sh', '.yaml', '.yml']
    
    # Directories to skip
    skip_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'env', 
        '.vscode', '.idea', 'build', 'dist', 'out', 'third_party',
        'depot_tools', '.gn', '.gclient', 'chromium-fetch'
    }
    
    # Files to skip
    skip_files = {'package-lock.json', 'yarn.lock'}
    
    files_processed = 0
    files_skipped = 0
    files_error = 0
    
    print(f"📁 Scanning: {base_dir}")
    print("")
    
    # Find all code files
    for ext in extensions:
        for file_path in base_dir.rglob(f'*{ext}'):
            # Skip if in skip directory
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue
            
            # Skip if in skip files
            if file_path.name in skip_files:
                continue
            
            # Skip very large files
            try:
                if file_path.stat().st_size > 1000000:  # 1MB
                    continue
            except:
                continue
            
            # Process file
            relative_path = file_path.relative_to(base_dir)
            success, message = add_copyright_to_file(file_path)
            
            if success:
                print(f"✅ {relative_path}")
                files_processed += 1
            elif "Already has copyright" in message:
                print(f"⏭️  {relative_path} (already has copyright)")
                files_skipped += 1
            else:
                print(f"⚠️  {relative_path}: {message}")
                files_error += 1
    
    print("")
    print("=" * 80)
    print("✅ COPYRIGHT NOTICES ADDED!")
    print("=" * 80)
    print("")
    print(f"📊 Summary:")
    print(f"   ✅ Files processed: {files_processed}")
    print(f"   ⏭️  Files skipped: {files_skipped}")
    print(f"   ⚠️  Errors: {files_error}")
    print("")
    print("🔒 Your code is now protected with copyright notices!")
    print("📋 Next: Create Terms of Service and License Agreement")

if __name__ == '__main__':
    main()

