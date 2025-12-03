#!/usr/bin/env python3
"""
Complete Website Assessment for phazevpn.duckdns.org
Checks everything: code, config, deployment, errors, etc.
"""

import sys
from pathlib import Path
import json
import subprocess
import os
import re
from datetime import datetime

BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / 'web-portal'
VPN_DIR = BASE_DIR if (BASE_DIR / 'vpn-manager.py').exists() else Path('/opt/secure-vpn')

print("=" * 80)
print("🔍 COMPLETE WEBSITE ASSESSMENT - phazevpn.duckdns.org")
print("=" * 80)
print("")

issues = []
warnings = []
info = []

# 1. Check if web portal exists
print("1️⃣  Checking Web Portal Files...")
if not WEB_PORTAL_DIR.exists():
    issues.append("❌ Web portal directory not found!")
else:
    info.append("✅ Web portal directory exists")
    
    app_py = WEB_PORTAL_DIR / 'app.py'
    if not app_py.exists():
        issues.append("❌ app.py not found!")
    else:
        info.append("✅ app.py exists")
        
        # Check file size
        size = app_py.stat().st_size
        if size > 300000:  # > 300KB
            warnings.append(f"⚠️  app.py is very large ({size/1024:.1f}KB) - might have performance issues")
        
        # Check for common issues in app.py
        content = app_py.read_text()
        
        # Check for hardcoded IPs
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        hardcoded_ips = re.findall(ip_pattern, content)
        if hardcoded_ips:
            unique_ips = list(set(hardcoded_ips))
            warnings.append(f"⚠️  Hardcoded IPs found: {', '.join(unique_ips)}")
        
        # Check for TODO/FIXME
        todos = re.findall(r'(TODO|FIXME|XXX|HACK|BUG)', content, re.IGNORECASE)
        if todos:
            warnings.append(f"⚠️  Found {len(todos)} TODO/FIXME comments in code")
        
        # Check for error handling
        if 'try:' in content and 'except:' in content:
            info.append("✅ Error handling present")
        else:
            warnings.append("⚠️  Limited error handling detected")

print("")

# 2. Check dependencies
print("2️⃣  Checking Dependencies...")
requirements = WEB_PORTAL_DIR / 'requirements.txt'
if requirements.exists():
    info.append("✅ requirements.txt exists")
    reqs = requirements.read_text().strip().split('\n')
    info.append(f"   Found {len(reqs)} dependencies")
    
    # Check if critical deps are listed
    critical = ['Flask', 'bcrypt', 'qrcode']
    for dep in critical:
        if any(dep.lower() in req.lower() for req in reqs):
            info.append(f"   ✅ {dep} listed")
        else:
            issues.append(f"❌ {dep} not in requirements.txt")
else:
    issues.append("❌ requirements.txt not found!")

print("")

# 3. Check configuration
print("3️⃣  Checking Configuration...")
users_file = VPN_DIR / 'users.json'
if users_file.exists():
    try:
        with open(users_file) as f:
            users_data = json.load(f)
            users = users_data.get('users', {})
            info.append(f"✅ Users file exists with {len(users)} users")
            
            # Check for default passwords
            default_users = ['admin', 'moderator', 'user']
            for username in default_users:
                if username in users:
                    user = users[username]
                    # Check if password is hashed (bcrypt starts with $2b$)
                    password = user.get('password', '')
                    if not password.startswith('$2b$') and not password.startswith('$2a$'):
                        warnings.append(f"⚠️  User '{username}' might have plaintext password!")
    except Exception as e:
        issues.append(f"❌ Error reading users.json: {e}")
else:
    warnings.append("⚠️  users.json not found - will use defaults")

# Check VPN config
vpn_config_file = BASE_DIR / 'vpn-manager.py'
if vpn_config_file.exists():
    vpn_content = vpn_config_file.read_text()
    if "'server_ip':" in vpn_content:
        # Extract server IP
        match = re.search(r"'server_ip':\s*['\"]([^'\"]+)['\"]", vpn_content)
        if match:
            server_ip = match.group(1)
            if server_ip:
                info.append(f"✅ Server IP configured: {server_ip}")
            else:
                warnings.append("⚠️  Server IP is empty - will auto-detect")
        else:
            warnings.append("⚠️  Could not parse server IP from config")

print("")

# 4. Check templates
print("4️⃣  Checking Templates...")
templates_dir = WEB_PORTAL_DIR / 'templates'
if templates_dir.exists():
    templates = list(templates_dir.glob('*.html'))
    info.append(f"✅ Found {len(templates)} HTML templates")
    
    # Check for critical templates
    critical_templates = ['login.html', 'signup.html', 'dashboard.html', 'base.html']
    for template in critical_templates:
        if (templates_dir / template).exists():
            info.append(f"   ✅ {template} exists")
        else:
            issues.append(f"❌ Critical template missing: {template}")
else:
    issues.append("❌ Templates directory not found!")

print("")

# 5. Check static files
print("5️⃣  Checking Static Files...")
static_dir = WEB_PORTAL_DIR / 'static'
if static_dir.exists():
    css_files = list(static_dir.glob('**/*.css'))
    js_files = list(static_dir.glob('**/*.js'))
    info.append(f"✅ Static files: {len(css_files)} CSS, {len(js_files)} JS")
else:
    warnings.append("⚠️  Static directory not found - CSS/JS might not work")

print("")

# 6. Check for common code issues
print("6️⃣  Checking Code Quality...")
if app_py.exists():
    content = app_py.read_text()
    
    # Check for SQL injection risks (if using SQL)
    if 'sql' in content.lower() and 'execute' in content.lower():
        if '?' not in content and '%s' not in content:
            warnings.append("⚠️  Possible SQL injection risk - check query building")
    
    # Check for XSS risks
    if 'render_template_string' in content:
        warnings.append("⚠️  render_template_string found - potential XSS risk if user input used")
    
    # Check for secret key
    if "app.secret_key = " in content:
        match = re.search(r"app\.secret_key = ['\"]([^'\"]+)['\"]", content)
        if match:
            secret = match.group(1)
            if len(secret) < 32:
                issues.append("❌ Secret key is too short (should be at least 32 chars)")
            elif secret == 'change-this-secret-key':
                issues.append("❌ Secret key is still default - CHANGE IT!")
            else:
                info.append("✅ Secret key configured")
    
    # Check for session security
    if "SESSION_COOKIE_SECURE" in content:
        if "SESSION_COOKIE_SECURE = False" in content:
            warnings.append("⚠️  SESSION_COOKIE_SECURE is False - cookies not secure over HTTP")
        else:
            info.append("✅ Session cookie security configured")
    
    # Check for CSRF protection
    if "CSRF" in content or "csrf" in content:
        info.append("✅ CSRF protection found")
    else:
        warnings.append("⚠️  No CSRF protection detected")

print("")

# 7. Check email configuration
print("7️⃣  Checking Email Configuration...")
email_files = [
    WEB_PORTAL_DIR / 'email_api.py',
    WEB_PORTAL_DIR / 'email_smtp.py',
    WEB_PORTAL_DIR / 'mailjet_config.py'
]
email_configured = False
for email_file in email_files:
    if email_file.exists():
        email_configured = True
        info.append(f"✅ {email_file.name} exists")
        break

if not email_configured:
    warnings.append("⚠️  No email configuration files found")

# Check for email API keys
if (WEB_PORTAL_DIR / 'mailjet_config.py').exists():
    mailjet_content = (WEB_PORTAL_DIR / 'mailjet_config.py').read_text()
    if 'API_KEY' in mailjet_content and 'API_SECRET' in mailjet_content:
        if 'YOUR_API_KEY' in mailjet_content or 'YOUR_SECRET' in mailjet_content:
            warnings.append("⚠️  Mailjet API keys appear to be placeholders")
        else:
            info.append("✅ Mailjet configuration present")

print("")

# 8. Check deployment status
print("8️⃣  Checking Deployment Status...")
# Check if nginx config exists
nginx_configs = [
    Path('/etc/nginx/sites-available/phazevpn'),
    Path('/etc/nginx/sites-enabled/phazevpn'),
    Path('/etc/nginx/conf.d/phazevpn.conf')
]
nginx_found = False
for nginx_config in nginx_configs:
    if nginx_config.exists():
        nginx_found = True
        info.append(f"✅ Nginx config found: {nginx_config}")
        break

if not nginx_found:
    warnings.append("⚠️  Nginx configuration not found - might not be deployed")

# Check for systemd service
systemd_services = [
    Path('/etc/systemd/system/phazevpn-portal.service'),
    Path('/etc/systemd/system/phazevpn-web.service'),
    Path('/lib/systemd/system/phazevpn-portal.service')
]
service_found = False
for service in systemd_services:
    if service.exists():
        service_found = True
        info.append(f"✅ Systemd service found: {service}")
        break

if not service_found:
    warnings.append("⚠️  Systemd service not found - portal might not be running as service")

print("")

# 9. Check for common Flask issues
print("9️⃣  Checking Flask Configuration...")
if app_py.exists():
    content = app_py.read_text()
    
    # Check debug mode
    if 'app.run(debug=True' in content or 'DEBUG = True' in content:
        issues.append("❌ DEBUG MODE IS ENABLED - SECURITY RISK!")
    else:
        info.append("✅ Debug mode not enabled")
    
    # Check port binding
    if 'app.run(host=' in content:
        match = re.search(r"app\.run\(host=['\"]?([^'\"]+)['\"]?", content)
        if match:
            host = match.group(1)
            if host == '0.0.0.0':
                info.append("✅ App binds to all interfaces")
            elif host == '127.0.0.1':
                warnings.append("⚠️  App only binds to localhost - won't be accessible externally")
    
    # Check for production WSGI
    if 'gunicorn' in content.lower() or 'waitress' in content.lower():
        info.append("✅ Production WSGI server mentioned")
    else:
        warnings.append("⚠️  No production WSGI server configured - using Flask dev server")

print("")

# 10. Check domain configuration
print("🔟 Checking Domain Configuration...")
domain_refs = []
if app_py.exists():
    content = app_py.read_text()
    # Find all domain references
    domain_pattern = r'phazevpn\.duckdns\.org'
    matches = re.findall(domain_pattern, content)
    if matches:
        info.append(f"✅ Found {len(matches)} references to phazevpn.duckdns.org")
    else:
        warnings.append("⚠️  No references to phazevpn.duckdns.org found in code")

print("")

# Summary
print("=" * 80)
print("📊 ASSESSMENT SUMMARY")
print("=" * 80)
print("")

if issues:
    print("❌ CRITICAL ISSUES:")
    for issue in issues:
        print(f"   {issue}")
    print("")

if warnings:
    print("⚠️  WARNINGS:")
    for warning in warnings:
        print(f"   {warning}")
    print("")

if info:
    print("✅ GOOD:")
    for item in info:
        print(f"   {item}")
    print("")

# Overall status
total_issues = len(issues)
total_warnings = len(warnings)

if total_issues == 0 and total_warnings == 0:
    print("🎉 EXCELLENT! No issues found!")
elif total_issues == 0:
    print(f"✅ GOOD! {total_warnings} warning(s) to review")
elif total_issues < 3:
    print(f"⚠️  NEEDS ATTENTION: {total_issues} critical issue(s), {total_warnings} warning(s)")
else:
    print(f"❌ CRITICAL: {total_issues} critical issue(s), {total_warnings} warning(s)")

print("")
print("=" * 80)
print("📝 RECOMMENDATIONS")
print("=" * 80)
print("")

recommendations = []

if total_issues > 0:
    recommendations.append("1. Fix all critical issues first")
if 'DEBUG MODE' in str(issues):
    recommendations.append("2. DISABLE DEBUG MODE immediately - security risk!")
if not nginx_found:
    recommendations.append("3. Set up Nginx reverse proxy for production")
if not service_found:
    recommendations.append("4. Create systemd service for automatic startup")
if 'SESSION_COOKIE_SECURE = False' in str(warnings):
    recommendations.append("5. Enable HTTPS and set SESSION_COOKIE_SECURE = True")
if 'hardcoded IPs' in str(warnings):
    recommendations.append("6. Replace hardcoded IPs with environment variables")

if recommendations:
    for i, rec in enumerate(recommendations, 1):
        print(f"   {rec}")
else:
    print("   ✅ No immediate recommendations - everything looks good!")

print("")
print("=" * 80)

