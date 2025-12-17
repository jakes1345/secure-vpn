#!/usr/bin/env python3
"""
Fix app.py errors and add comprehensive security hardening
"""

import paramiko
import re

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 FIXING APP.PY AND ADDING SECURITY")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Read app.py
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
            content = f.read().decode('utf-8')
    except Exception as e:
        print(f"   ❌ Error reading app.py: {e}")
        sftp.close()
        ssh.close()
        return
    
    # Fix 1: Add login_required decorator
    if 'def login_required' not in content:
        # Add after require_permission
        require_permission_pos = content.find('def require_permission')
        if require_permission_pos > 0:
            # Find end of require_permission function
            end_pos = content.find('\n\n', require_permission_pos + 100)
            if end_pos > 0:
                login_required_code = '''

def login_required(f):
    """Decorator to require login (for API endpoints)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

'''
                content = content[:end_pos] + login_required_code + content[end_pos:]
                print("   ✅ Added login_required decorator")
    
    # Fix 2: Replace @login_required with @require_api_auth for API endpoints
    # Actually, let's keep login_required but make sure it's defined
    
    # Fix 3: Add comprehensive security headers and rate limiting
    security_code = '''
# ============================================
# SECURITY HARDENING
# ============================================

from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
import time

# Rate limiting storage
_rate_limit_storage = defaultdict(list)
_rate_limit_cleanup_time = time.time()

def cleanup_rate_limits():
    """Clean up old rate limit entries"""
    global _rate_limit_cleanup_time
    current_time = time.time()
    if current_time - _rate_limit_cleanup_time > 300:  # Every 5 minutes
        cutoff = current_time - 3600  # 1 hour
        for key in list(_rate_limit_storage.keys()):
            _rate_limit_storage[key] = [t for t in _rate_limit_storage[key] if t > cutoff]
            if not _rate_limit_storage[key]:
                del _rate_limit_storage[key]
        _rate_limit_cleanup_time = current_time

def rate_limit(max_requests=10, window=60, per_ip=True):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cleanup_rate_limits()
            
            # Get client identifier
            if per_ip:
                client_id = request.remote_addr
            else:
                client_id = session.get('username', request.remote_addr)
            
            # Check rate limit
            current_time = time.time()
            window_start = current_time - window
            
            # Filter requests in window
            requests = [t for t in _rate_limit_storage[client_id] if t > window_start]
            
            if len(requests) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Maximum {max_requests} requests per {window} seconds.'
                }), 429
            
            # Add current request
            requests.append(current_time)
            _rate_limit_storage[client_id] = requests
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(data, required_fields=None, max_lengths=None):
    """Validate and sanitize input"""
    if required_fields:
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f'Missing required field: {field}'
    
    if max_lengths:
        for field, max_len in max_lengths.items():
            if field in data and len(str(data[field])) > max_len:
                return False, f'Field {field} exceeds maximum length of {max_len}'
    
    # Basic XSS protection
    for key, value in data.items():
        if isinstance(value, str):
            # Remove script tags and dangerous patterns
            value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
            value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
            data[key] = value
    
    return True, None

# Enhanced security headers
@app.after_request
def set_enhanced_security_headers(response):
    """Add comprehensive security headers"""
    # Existing headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Server'] = ''
    
    # Additional security headers
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';"
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    return response

# IP whitelist for admin endpoints (optional - can be disabled)
ADMIN_IP_WHITELIST = []  # Empty = no IP restriction

def check_admin_ip():
    """Check if admin request is from whitelisted IP"""
    if not ADMIN_IP_WHITELIST:
        return True  # No restriction
    
    client_ip = request.remote_addr
    return client_ip in ADMIN_IP_WHITELIST

'''
    
    # Insert security code after imports
    if 'def rate_limit' not in content:
        # Find a good place to insert (after existing security headers)
        security_headers_pos = content.find('@app.after_request')
        if security_headers_pos > 0:
            # Find end of that function
            end_pos = content.find('\n\n', security_headers_pos + 200)
            if end_pos > 0:
                content = content[:end_pos] + security_code + content[end_pos:]
                print("   ✅ Added security hardening")
    
    # Fix 4: Add error handling to prevent 500 errors
    error_handler_code = '''
# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('error.html', message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"Internal Server Error: {error_trace}")
    
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred processing your request'
        }), 500
    
    return render_template('error.html', 
        message='An internal error occurred. Please try again later.'), 500

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('error.html', message='Access denied'), 403

@app.errorhandler(429)
def rate_limit_error(error):
    """Handle rate limit errors"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429
'''
    
    # Add error handlers before app.run
    if '@app.errorhandler(500)' not in content:
        main_pos = content.rfind("if __name__ == '__main__':")
        if main_pos > 0:
            content = content[:main_pos] + error_handler_code + '\n' + content[main_pos:]
            print("   ✅ Added error handlers")
    
    # Fix 5: Add rate limiting to sensitive endpoints
    # This will be done by updating specific routes
    
    # Write back
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
        f.write(content.encode('utf-8'))
    sftp.close()
    
    print("\n   ✅ App.py fixed!")
    
    # Test if it works
    print("\n🔍 Testing app.py...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 -c "import app; print(\"OK\")" 2>&1')
    output = stdout.read().decode()
    if 'OK' in output:
        print("   ✅ App.py imports successfully!")
    else:
        print(f"   ⚠️  Error: {output[:500]}")
    
    ssh.close()

if __name__ == "__main__":
    main()

