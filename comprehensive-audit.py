#!/usr/bin/env python3
"""
Comprehensive Codebase Audit Script
Checks for missing files, routes, static assets, dependencies, and VPS sync completeness
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json

# Base paths
BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / 'web-portal'
TEMPLATES_DIR = WEB_PORTAL_DIR / 'templates'
STATIC_DIR = WEB_PORTAL_DIR / 'static'
APP_PY = WEB_PORTAL_DIR / 'app.py'

# Results storage
issues = {
    'missing_static_files': [],
    'missing_templates': [],
    'missing_routes': [],
    'missing_dependencies': [],
    'missing_config_files': [],
    'vps_sync_missing': [],
    'orphaned_files': [],
    'broken_references': []
}

# Track what exists
existing_static = set()
existing_templates = set()
existing_routes = set()

print("=" * 80)
print("COMPREHENSIVE CODEBASE AUDIT")
print("=" * 80)
print()

# ============================================
# 1. SCAN EXISTING FILES
# ============================================
print("[1/7] Scanning existing files...")

# Static files
if STATIC_DIR.exists():
    for file_path in STATIC_DIR.rglob('*'):
        if file_path.is_file():
            rel_path = file_path.relative_to(STATIC_DIR)
            existing_static.add(str(rel_path).replace('\\', '/'))

# Templates
if TEMPLATES_DIR.exists():
    for file_path in TEMPLATES_DIR.rglob('*.html'):
        rel_path = file_path.relative_to(TEMPLATES_DIR)
        existing_templates.add(str(rel_path).replace('\\', '/'))

print(f"   Found {len(existing_static)} static files")
print(f"   Found {len(existing_templates)} templates")
print()

# ============================================
# 2. CHECK STATIC FILES REFERENCED IN TEMPLATES
# ============================================
print("[2/7] Checking static file references in templates...")

static_patterns = [
    r"url_for\('static',\s*filename=['\"]([^'\"]+)['\"]\)",
    r"url_for\(['\"]static['\"],\s*filename=['\"]([^'\"]+)['\"]\)",
    r"/static/([^\s\"'<>]+)",
    r"static/([^\s\"'<>]+)",
]

referenced_static = set()

if TEMPLATES_DIR.exists():
    for template_file in TEMPLATES_DIR.rglob('*.html'):
        try:
            content = template_file.read_text(encoding='utf-8')
            for pattern in static_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up the path
                    path = match.strip().strip("'\"")
                    if path and not path.startswith('http'):
                        referenced_static.add(path)
        except Exception as e:
            print(f"   ⚠️  Error reading {template_file}: {e}")

# Check for missing static files
for ref in referenced_static:
    if ref not in existing_static:
        issues['missing_static_files'].append({
            'file': ref,
            'referenced_in': 'templates'
        })

print(f"   Found {len(referenced_static)} static file references")
if issues['missing_static_files']:
    print(f"   ❌ Missing {len(issues['missing_static_files'])} static files")
else:
    print(f"   ✅ All referenced static files exist")
print()

# ============================================
# 3. CHECK TEMPLATES REFERENCED IN ROUTES
# ============================================
print("[3/7] Checking template references in app.py...")

template_patterns = [
    r"render_template\(['\"]([^'\"]+)['\"]",
    r"render_template\(['\"]([^'\"]+)['\"],",
]

referenced_templates = set()

if APP_PY.exists():
    try:
        content = APP_PY.read_text(encoding='utf-8')
        for pattern in template_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                template_path = match.strip().strip("'\"")
                if template_path:
                    referenced_templates.add(template_path)
    except Exception as e:
        print(f"   ⚠️  Error reading app.py: {e}")

# Check for missing templates
for ref in referenced_templates:
    if ref not in existing_templates:
        issues['missing_templates'].append({
            'template': ref,
            'referenced_in': 'app.py'
        })

print(f"   Found {len(referenced_templates)} template references")
if issues['missing_templates']:
    print(f"   ❌ Missing {len(issues['missing_templates'])} templates")
else:
    print(f"   ✅ All referenced templates exist")
print()

# ============================================
# 4. CHECK ROUTES DEFINED IN APP.PY
# ============================================
print("[4/7] Checking route definitions...")

route_patterns = [
    r"@app\.route\(['\"]([^'\"]+)['\"]",
    r"@app\.route\(['\"]([^'\"]+)['\"],\s*methods=",
]

if APP_PY.exists():
    try:
        content = APP_PY.read_text(encoding='utf-8')
        for pattern in route_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                route = match.strip()
                if route:
                    existing_routes.add(route)
    except Exception as e:
        print(f"   ⚠️  Error reading app.py: {e}")

print(f"   Found {len(existing_routes)} route definitions")
print()

# ============================================
# 5. CHECK DEPENDENCIES
# ============================================
print("[5/7] Checking dependencies...")

requirements_file = WEB_PORTAL_DIR / 'requirements.txt'
imports_in_app = set()

if APP_PY.exists():
    try:
        content = APP_PY.read_text(encoding='utf-8')
        # Find import statements
        import_patterns = [
            r"^import\s+(\w+)",
            r"^from\s+(\w+)",
            r"from\s+(\w+)\s+import",
        ]
        for line in content.split('\n'):
            for pattern in import_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    module = match.group(1).split('.')[0]
                    imports_in_app.add(module)
    except Exception as e:
        print(f"   ⚠️  Error reading app.py: {e}")

# Check requirements.txt
required_packages = set()
if requirements_file.exists():
    try:
        content = requirements_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before == or >= etc)
                pkg = re.split(r'[>=<!=]', line)[0].strip()
                if pkg:
                    required_packages.add(pkg.lower())
    except Exception as e:
        print(f"   ⚠️  Error reading requirements.txt: {e}")

# Common Python stdlib modules (don't need to be in requirements)
stdlib_modules = {
    'os', 'sys', 'json', 'pathlib', 'datetime', 'time', 're', 'hashlib',
    'secrets', 'io', 'base64', 'subprocess', 'collections', 'functools',
    'urllib', 'email', 'csv', 'shlex', 'traceback', 'logging', 'threading'
}

# Check for missing dependencies
for imp in imports_in_app:
    if imp.lower() not in required_packages and imp.lower() not in stdlib_modules:
        # Check if it's a local import
        if not (WEB_PORTAL_DIR / f"{imp}.py").exists():
            issues['missing_dependencies'].append({
                'module': imp,
                'imported_in': 'app.py'
            })

print(f"   Found {len(imports_in_app)} imports")
print(f"   Found {len(required_packages)} packages in requirements.txt")
if issues['missing_dependencies']:
    print(f"   ⚠️  Potential missing dependencies: {len(issues['missing_dependencies'])}")
else:
    print(f"   ✅ Dependencies look good")
print()

# ============================================
# 6. CHECK CONFIGURATION FILES
# ============================================
print("[6/7] Checking configuration files...")

config_files_needed = [
    'db_config.json',  # MySQL config
    '.env',  # Environment variables
    'nginx-phazevpn.conf',  # Nginx config
]

for config_file in config_files_needed:
    config_path = WEB_PORTAL_DIR / config_file
    if not config_path.exists():
        issues['missing_config_files'].append({
            'file': config_file,
            'location': str(config_path)
        })

print(f"   Checked {len(config_files_needed)} config files")
if issues['missing_config_files']:
    print(f"   ⚠️  Missing {len(issues['missing_config_files'])} config files")
else:
    print(f"   ✅ All config files exist")
print()

# ============================================
# 7. CHECK VPS SYNC SCRIPTS
# ============================================
print("[7/7] Checking VPS sync script completeness...")

sync_scripts = [
    BASE_DIR / 'sync-to-vps.sh',
    BASE_DIR / 'SYNC-TO-VPS.sh',
]

critical_files_for_vps = [
    'web-portal/app.py',
    'web-portal/requirements.txt',
    'web-portal/templates/base.html',
    'web-portal/static/css/style.css',
    'web-portal/static/js/main.js',
    'web-portal/static/images/logo-optimized.png',
    'web-portal/static/images/favicon.png',
]

for sync_script in sync_scripts:
    if sync_script.exists():
        try:
            content = sync_script.read_text(encoding='utf-8')
            for critical_file in critical_files_for_vps:
                file_path = BASE_DIR / critical_file
                if file_path.exists():
                    # Check if sync script mentions this file
                    file_name = Path(critical_file).name
                    if file_name not in content and critical_file not in content:
                        issues['vps_sync_missing'].append({
                            'file': critical_file,
                            'sync_script': sync_script.name
                        })
        except Exception as e:
            print(f"   ⚠️  Error reading {sync_script}: {e}")

print(f"   Checked {len(sync_scripts)} sync scripts")
if issues['vps_sync_missing']:
    print(f"   ⚠️  {len(issues['vps_sync_missing'])} files may not be synced")
else:
    print(f"   ✅ Sync scripts look complete")
print()

# ============================================
# GENERATE REPORT
# ============================================
print("=" * 80)
print("AUDIT SUMMARY")
print("=" * 80)
print()

total_issues = sum(len(v) for v in issues.values())

if total_issues == 0:
    print("✅ NO ISSUES FOUND! Codebase looks complete.")
else:
    print(f"⚠️  FOUND {total_issues} POTENTIAL ISSUES:")
    print()

    if issues['missing_static_files']:
        print(f"❌ MISSING STATIC FILES ({len(issues['missing_static_files'])}):")
        for item in issues['missing_static_files'][:10]:  # Show first 10
            print(f"   - {item['file']}")
        if len(issues['missing_static_files']) > 10:
            print(f"   ... and {len(issues['missing_static_files']) - 10} more")
        print()

    if issues['missing_templates']:
        print(f"❌ MISSING TEMPLATES ({len(issues['missing_templates'])}):")
        for item in issues['missing_templates']:
            print(f"   - {item['template']}")
        print()

    if issues['missing_dependencies']:
        print(f"⚠️  POTENTIAL MISSING DEPENDENCIES ({len(issues['missing_dependencies'])}):")
        for item in issues['missing_dependencies'][:10]:
            print(f"   - {item['module']} (imported in {item['imported_in']})")
        if len(issues['missing_dependencies']) > 10:
            print(f"   ... and {len(issues['missing_dependencies']) - 10} more")
        print()

    if issues['missing_config_files']:
        print(f"⚠️  MISSING CONFIG FILES ({len(issues['missing_config_files'])}):")
        for item in issues['missing_config_files']:
            print(f"   - {item['file']} (expected at {item['location']})")
        print()

    if issues['vps_sync_missing']:
        print(f"⚠️  FILES NOT IN SYNC SCRIPTS ({len(issues['vps_sync_missing'])}):")
        for item in issues['vps_sync_missing'][:10]:
            print(f"   - {item['file']} (not in {item['sync_script']})")
        if len(issues['vps_sync_missing']) > 10:
            print(f"   ... and {len(issues['vps_sync_missing']) - 10} more")
        print()

# Save detailed report
report_file = BASE_DIR / 'AUDIT-REPORT.json'
with open(report_file, 'w') as f:
    json.dump({
        'summary': {
            'total_issues': total_issues,
            'missing_static_files': len(issues['missing_static_files']),
            'missing_templates': len(issues['missing_templates']),
            'missing_dependencies': len(issues['missing_dependencies']),
            'missing_config_files': len(issues['missing_config_files']),
            'vps_sync_missing': len(issues['vps_sync_missing']),
        },
        'issues': issues,
        'existing': {
            'static_files': len(existing_static),
            'templates': len(existing_templates),
            'routes': len(existing_routes),
        }
    }, f, indent=2)

print(f"📄 Detailed report saved to: {report_file}")
print()

# ============================================
# RECOMMENDATIONS
# ============================================
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

recommendations = []

if issues['missing_static_files']:
    recommendations.append("Create missing static files or update template references")

if issues['missing_templates']:
    recommendations.append("Create missing templates or fix route references")

if issues['missing_config_files']:
    recommendations.append("Create missing configuration files (db_config.json, .env, etc.)")

if issues['vps_sync_missing']:
    recommendations.append("Update VPS sync scripts to include all critical files")

if recommendations:
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
else:
    print("✅ No immediate recommendations. Codebase looks good!")

print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
