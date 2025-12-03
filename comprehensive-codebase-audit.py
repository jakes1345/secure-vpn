#!/usr/bin/env python3
"""
Comprehensive Codebase Audit
Finds incorrect configurations, hardcoded values, and potential issues
"""

import os
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/media/jack/Liunux/secure-vpn")

# Issues to check for
ISSUES = {
    'local_paths': {
        'patterns': [
            r'/media/jack/',
            r'/home/jack/',
            r'jack-MS-7C95',
            r'jack@jack',
        ],
        'description': 'Hardcoded local PC paths (should use VPS paths)',
        'severity': 'HIGH'
    },
    'hardcoded_ips': {
        'patterns': [
            r'15\.204\.11\.19',  # VPS IP - should be configurable
            r'46\.110\.121\.128',  # Old IP
            r'192\.168\.86\.39',  # Local network IP
        ],
        'description': 'Hardcoded IP addresses (should use domain or config)',
        'severity': 'MEDIUM'
    },
    'wrong_0_0_0_0': {
        'patterns': [
            r'Server\s*=\s*0\.0\.0\.0',
            r'server\s*=\s*0\.0\.0\.0[^/]',  # Not 0.0.0.0/0
            r'remote\s+0\.0\.0\.0',
            r'connect.*0\.0\.0\.0',
        ],
        'description': '0.0.0.0 in client configs (clients need real server address)',
        'severity': 'HIGH'
    },
    'hardcoded_credentials': {
        'patterns': [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'PASSWORD\s*=\s*["\'][^"\']+["\']',
            r'passwd\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'API_KEY\s*=\s*["\'][^"\']+["\']',
        ],
        'description': 'Hardcoded passwords/secrets (should use env vars)',
        'severity': 'CRITICAL'
    },
    'wrong_ports': {
        'patterns': [
            r':8000',  # User doesn't want port 8000
        ],
        'description': 'Port 8000 usage (user preference: avoid)',
        'severity': 'LOW'
    },
    'todo_fixme': {
        'patterns': [
            r'TODO',
            r'FIXME',
            r'XXX',
            r'HACK',
            r'BUG',
        ],
        'description': 'TODO/FIXME comments (unfinished work)',
        'severity': 'MEDIUM'
    },
    'deprecated_code': {
        'patterns': [
            r'@deprecated',
            r'deprecated',
            r'legacy',
            r'old_',
        ],
        'description': 'Deprecated/legacy code',
        'severity': 'MEDIUM'
    },
    'print_statements': {
        'patterns': [
            r'print\s*\(',
        ],
        'description': 'print() statements (should use logging)',
        'severity': 'LOW'
    },
    'debug_mode': {
        'patterns': [
            r'debug\s*=\s*True',
            r'DEBUG\s*=\s*True',
        ],
        'description': 'Debug mode enabled (security risk in production)',
        'severity': 'HIGH'
    },
    'insecure_ssl': {
        'patterns': [
            r'verify\s*=\s*False',
            r'SSL_VERIFY\s*=\s*False',
            r'disable.*ssl',
            r'disable.*warning',
        ],
        'description': 'SSL verification disabled (security risk)',
        'severity': 'HIGH'
    },
    'sql_injection_risk': {
        'patterns': [
            r'execute\s*\(.*\+',
            r'query\s*\(.*\+',
            r'f["\'].*SELECT.*\{',
            r'f["\'].*INSERT.*\{',
        ],
        'description': 'Potential SQL injection risks',
        'severity': 'CRITICAL'
    },
    'missing_error_handling': {
        'patterns': [
            r'open\([^)]+\)\s*$',  # File open without try/except
            r'subprocess\.run\([^)]+\)\s*$',  # Subprocess without error handling
        ],
        'description': 'Missing error handling',
        'severity': 'MEDIUM'
    },
}

# Files to skip
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
    r'\.png$',
    r'\.jpg$',
    r'\.jpeg$',
    r'\.gif$',
    r'\.ico$',
    r'\.pdf$',
    r'\.zip$',
    r'\.tar$',
    r'\.gz$',
    r'comprehensive-codebase-audit\.py',  # Skip this file
]

def should_skip_file(filepath):
    """Check if file should be skipped"""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, str(filepath), re.IGNORECASE):
            return True
    return False

def find_issues():
    """Find all issues in codebase"""
    results = defaultdict(list)
    
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
                    
                    for issue_type, issue_config in ISSUES.items():
                        for pattern in issue_config['patterns']:
                            for line_num, line in enumerate(lines, 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    # Skip if it's in a comment explaining the issue
                                    if 'should' in line.lower() or 'note:' in line.lower() or '# ' in line[:20]:
                                        continue
                                    
                                    rel_path = filepath.relative_to(BASE_DIR)
                                    entry = {
                                        'file': str(rel_path),
                                        'line': line_num,
                                        'content': line.strip()[:120],
                                        'severity': issue_config['severity']
                                    }
                                    
                                    # Avoid duplicates
                                    if entry not in results[issue_type]:
                                        results[issue_type].append(entry)
            except Exception as e:
                # Skip files we can't read
                continue
    
    return results

def main():
    print("=" * 70)
    print("🔍 COMPREHENSIVE CODEBASE AUDIT")
    print("=" * 70)
    print()
    print("Scanning entire codebase for issues...")
    print("This may take a minute...")
    print()
    
    results = find_issues()
    
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    
    print("=" * 70)
    print("📊 AUDIT RESULTS")
    print("=" * 70)
    print()
    
    # Group by severity
    by_severity = defaultdict(list)
    for issue_type, entries in results.items():
        if entries:
            severity = entries[0]['severity']
            by_severity[severity].append((issue_type, entries))
    
    # Print by severity
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if severity in by_severity:
            print(f"\n{'='*70}")
            print(f"🔴 {severity} SEVERITY ISSUES")
            print(f"{'='*70}")
            print()
            
            for issue_type, entries in by_severity[severity]:
                issue_config = ISSUES[issue_type]
                print(f"📋 {issue_config['description']} ({len(entries)} found)")
                print(f"   Severity: {severity}")
                print()
                
                # Show first 10 examples
                for entry in entries[:10]:
                    print(f"   {entry['file']}:{entry['line']}")
                    print(f"      {entry['content']}")
                    print()
                
                if len(entries) > 10:
                    print(f"   ... and {len(entries) - 10} more")
                    print()
    
    # Summary
    print("=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print()
    
    total_issues = sum(len(entries) for entries in results.values())
    critical = sum(len(entries) for entries in results.values() if entries and entries[0]['severity'] == 'CRITICAL')
    high = sum(len(entries) for entries in results.values() if entries and entries[0]['severity'] == 'HIGH')
    medium = sum(len(entries) for entries in results.values() if entries and entries[0]['severity'] == 'MEDIUM')
    low = sum(len(entries) for entries in results.values() if entries and entries[0]['severity'] == 'LOW')
    
    print(f"   🔴 CRITICAL: {critical}")
    print(f"   🟠 HIGH: {high}")
    print(f"   🟡 MEDIUM: {medium}")
    print(f"   🟢 LOW: {low}")
    print(f"   📊 TOTAL: {total_issues}")
    print()
    
    if critical > 0 or high > 0:
        print("⚠️  ACTION REQUIRED:")
        print("   Fix CRITICAL and HIGH severity issues first!")
        print()
    else:
        print("✅ No critical issues found!")
        print()
    
    # Detailed breakdown
    print("=" * 70)
    print("📊 DETAILED BREAKDOWN")
    print("=" * 70)
    print()
    
    for issue_type, entries in sorted(results.items(), key=lambda x: len(x[1]), reverse=True):
        if entries:
            issue_config = ISSUES[issue_type]
            print(f"   {issue_type}: {len(entries)} issues ({issue_config['severity']})")
    
    print()

if __name__ == "__main__":
    main()

