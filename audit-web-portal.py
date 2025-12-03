#!/usr/bin/env python3
"""
Comprehensive Web Portal Audit
Checks for issues, missing features, broken links, etc.
"""

import os
import sys
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy
import re

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / "web-portal"
TEMPLATES_DIR = WEB_PORTAL_DIR / "templates"

print("=" * 70)
print("🔍 COMPREHENSIVE WEB PORTAL AUDIT")
print("=" * 70)
print("")

issues = []
warnings = []
improvements = []

# 1. Check all routes have templates
print("1️⃣ Checking routes and templates...")
try:
    with open(WEB_PORTAL_DIR / "app.py", "r") as f:
        app_content = f.read()
    
    # Find all routes
    routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", app_content)
    print(f"   Found {len(routes)} routes")
    
    # Find all render_template calls
    templates = re.findall(r"render_template\(['\"]([^'\"]+)['\"]", app_content)
    print(f"   Found {len(templates)} template references")
    
    # Check if templates exist
    missing_templates = []
    for template in templates:
        template_path = TEMPLATES_DIR / template
        if not template_path.exists():
            missing_templates.append(template)
            issues.append(f"❌ Missing template: {template}")
    
    if missing_templates:
        print(f"   ⚠️  {len(missing_templates)} missing templates")
    else:
        print("   ✅ All templates exist")
        
except Exception as e:
    issues.append(f"❌ Error checking routes: {e}")

print("")

# 2. Check for broken imports
print("2️⃣ Checking imports and dependencies...")
try:
    missing_imports = []
    required_modules = [
        'flask', 'bcrypt', 'qrcode', 'paramiko', 'stripe'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_imports.append(module)
            warnings.append(f"⚠️  Missing module: {module}")
    
    if missing_imports:
        print(f"   ⚠️  {len(missing_imports)} missing modules: {', '.join(missing_imports)}")
    else:
        print("   ✅ All required modules available")
        
except Exception as e:
    issues.append(f"❌ Error checking imports: {e}")

print("")

# 3. Check static files
print("3️⃣ Checking static files...")
static_dir = WEB_PORTAL_DIR / "static"
if static_dir.exists():
    static_files = list(static_dir.rglob("*"))
    print(f"   Found {len(static_files)} static files")
    
    # Check for common missing files
    common_static = ['css', 'js', 'images']
    for item in common_static:
        item_path = static_dir / item
        if not item_path.exists():
            improvements.append(f"💡 Consider adding: static/{item}/ directory")
else:
    warnings.append("⚠️  No static directory found")
    print("   ⚠️  No static directory")

print("")

# 4. Check security features
print("4️⃣ Checking security features...")
security_features = {
    'bcrypt': 'bcrypt' in app_content,
    'session_security': 'SESSION_COOKIE_SECURE' in app_content,
    'csrf_protection': 'CSRFProtect' in app_content or 'csrf' in app_content.lower(),
    'rate_limiting': 'rate_limit' in app_content or 'limiter' in app_content.lower(),
    'input_validation': 'validate' in app_content.lower() or 'sanitize' in app_content.lower(),
    'sql_injection_protection': 'parameterized' in app_content.lower() or 'execute' not in app_content or '?' in app_content,
}

for feature, present in security_features.items():
    if present:
        print(f"   ✅ {feature}")
    else:
        warnings.append(f"⚠️  Missing security feature: {feature}")

print("")

# 5. Check for hardcoded values
print("5️⃣ Checking for hardcoded values...")
hardcoded_patterns = [
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
    (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
    (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
]

found_hardcoded = []
for pattern, desc in hardcoded_patterns:
    matches = re.findall(pattern, app_content, re.IGNORECASE)
    if matches:
        found_hardcoded.append(f"{desc}: {len(matches)} instances")
        warnings.append(f"⚠️  {desc} found")

if found_hardcoded:
    print(f"   ⚠️  Found {len(found_hardcoded)} hardcoded values")
else:
    print("   ✅ No obvious hardcoded secrets")

print("")

# 6. Check error handling
print("6️⃣ Checking error handling...")
error_handlers = [
    '@app.errorhandler(404)',
    '@app.errorhandler(500)',
    '@app.errorhandler(403)',
]

for handler in error_handlers:
    if handler in app_content:
        print(f"   ✅ {handler}")
    else:
        warnings.append(f"⚠️  Missing error handler: {handler}")

# Check for try/except blocks
try_except_count = len(re.findall(r"try\s*:", app_content))
print(f"   Found {try_except_count} try/except blocks")

print("")

# 7. Check API endpoints
print("7️⃣ Checking API endpoints...")
api_routes = [r for r in routes if r.startswith('/api/')]
print(f"   Found {len(api_routes)} API endpoints")

# Check for API authentication
api_auth = 'login_required' in app_content or '@require_login' in app_content
if api_auth:
    print("   ✅ API authentication present")
else:
    warnings.append("⚠️  API endpoints may not have authentication")

print("")

# 8. Check database/user management
print("8️⃣ Checking user management...")
user_features = {
    'user_registration': '/signup' in routes,
    'password_reset': '/forgot-password' in routes,
    '2fa': '/2fa' in app_content,
    'session_management': 'session' in app_content.lower(),
}

for feature, present in user_features.items():
    if present:
        print(f"   ✅ {feature}")
    else:
        improvements.append(f"💡 Consider adding: {feature}")

print("")

# 9. Check payment integration
print("9️⃣ Checking payment integration...")
payment_features = {
    'stripe': 'stripe' in app_content.lower(),
    'payment_page': '/payment' in routes,
    'webhook': '/webhook' in routes,
}

for feature, present in payment_features.items():
    if present:
        print(f"   ✅ {feature}")
    else:
        improvements.append(f"💡 Consider adding: {feature}")

print("")

# 10. Check for TODO/FIXME comments
print("🔟 Checking for TODO/FIXME comments...")
todos = re.findall(r"(TODO|FIXME|XXX|HACK|BUG):\s*(.+)", app_content, re.IGNORECASE)
if todos:
    print(f"   ⚠️  Found {len(todos)} TODO/FIXME comments")
    for todo in todos[:5]:  # Show first 5
        warnings.append(f"⚠️  {todo[0]}: {todo[1][:50]}")
else:
    print("   ✅ No TODO/FIXME comments found")

print("")

# 11. Check VPS deployment
print("1️⃣1️⃣ Checking VPS deployment...")
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Check if web portal is running
    stdin, stdout, stderr = ssh.exec_command("pgrep -f app.py && echo 'Running' || echo 'NOT RUNNING'")
    portal_status = stdout.read().decode().strip()
    
    if "Running" in portal_status:
        print("   ✅ Web portal is running")
    else:
        issues.append("❌ Web portal is NOT running on VPS")
    
    # Check port
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp | grep 8081")
    port_check = stdout.read().decode().strip()
    if port_check:
        print("   ✅ Port 8081 is listening")
    else:
        issues.append("❌ Port 8081 is not listening")
    
    # Check nginx
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx")
    nginx_status = stdout.read().decode().strip()
    if nginx_status == "active":
        print("   ✅ Nginx is active")
    else:
        warnings.append("⚠️  Nginx is not active")
    
    ssh.close()
    
except Exception as e:
    warnings.append(f"⚠️  Could not check VPS: {e}")

print("")

# 12. Check for missing features compared to professional VPN sites
print("1️⃣2️⃣ Checking for missing professional features...")
professional_features = {
    'Server selection': '/api/app/servers' in routes,
    'Connection status': '/api/app/connection-status' in routes,
    'Data usage tracking': '/api/stats/bandwidth' in routes,
    'Mobile app support': '/mobile' in app_content,
    'FAQ page': '/faq' in routes,
    'Privacy policy': '/privacy' in routes,
    'Terms of service': '/terms' in routes,
    'Contact page': '/contact' in routes,
    'Blog/News': '/blog' in routes,
    'Testimonials': '/testimonials' in routes,
    'Pricing page': '/pricing' in routes,
    'SEO (sitemap)': '/sitemap.xml' in routes,
    'SEO (robots.txt)': '/robots.txt' in routes,
}

missing_features = []
for feature, present in professional_features.items():
    if present:
        print(f"   ✅ {feature}")
    else:
        missing_features.append(feature)
        improvements.append(f"💡 Missing feature: {feature}")

if missing_features:
    print(f"   ⚠️  {len(missing_features)} features missing")

print("")

# Summary
print("=" * 70)
print("📊 AUDIT SUMMARY")
print("=" * 70)
print("")

if issues:
    print(f"❌ CRITICAL ISSUES ({len(issues)}):")
    for issue in issues:
        print(f"   {issue}")
    print("")

if warnings:
    print(f"⚠️  WARNINGS ({len(warnings)}):")
    for warning in warnings[:10]:  # Show first 10
        print(f"   {warning}")
    if len(warnings) > 10:
        print(f"   ... and {len(warnings) - 10} more")
    print("")

if improvements:
    print(f"💡 IMPROVEMENTS ({len(improvements)}):")
    for improvement in improvements[:10]:  # Show first 10
        print(f"   {improvement}")
    if len(improvements) > 10:
        print(f"   ... and {len(improvements) - 10} more")
    print("")

print("=" * 70)
print("✅ AUDIT COMPLETE")
print("=" * 70)

