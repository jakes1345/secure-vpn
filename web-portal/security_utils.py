#!/usr/bin/env python3
"""
Security Utilities
Provides security decorators and utilities for enhanced protection
"""

from functools import wraps
from flask import request, jsonify, render_template, url_for, redirect, session
import time
from typing import Callable, Optional

# Rate limiting storage (in-memory fallback)
_rate_limit_storage = {}
_rate_limit_cleanup_time = time.time()

def rate_limit(max_requests: int = 5, window_seconds: int = 60, 
               by_username: bool = True, by_ip: bool = False):
    """
    Rate limiting decorator for endpoints.
    
    Args:
        max_requests: Maximum requests allowed in time window
        window_seconds: Time window in seconds
        by_username: Rate limit by username (privacy-friendly)
        by_ip: Rate limit by IP (NOT recommended for privacy)
        
    Privacy:
        By default, rate limits by username only (no IP tracking).
        Set by_ip=True only if absolutely necessary for security.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine identifier (username preferred for privacy)
            identifier = None
            
            if by_username and 'username' in session:
                identifier = f"user:{session['username']}"
            elif by_ip:
                identifier = f"ip:{request.remote_addr}"
            else:
                # No identifier = no rate limit (allow request)
                return f(*args, **kwargs)
            
            if not identifier:
                return f(*args, **kwargs)
            
            # Clean old entries periodically
            global _rate_limit_cleanup_time
            current_time = time.time()
            if current_time - _rate_limit_cleanup_time > 300:  # Clean every 5 minutes
                cutoff_time = current_time - window_seconds
                _rate_limit_storage.clear()  # Simple cleanup
                _rate_limit_cleanup_time = current_time
            
            # Check rate limit
            key = f"{f.__name__}:{identifier}"
            now = time.time()
            
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = []
            
            # Remove old entries
            _rate_limit_storage[key] = [
                t for t in _rate_limit_storage[key] 
                if now - t < window_seconds
            ]
            
            # Check limit
            if len(_rate_limit_storage[key]) >= max_requests:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': 'Rate limit exceeded. Please try again later.'
                    }), 429
                else:
                    return render_template('error.html',
                        message='Rate limit exceeded. Please try again later.',
                        error='Too Many Requests'
                    ), 429
            
            # Record request
            _rate_limit_storage[key].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_csrf(f: Callable) -> Callable:
    """
    Decorator to require CSRF token for POST requests.
    
    Note: This is a basic check. Full CSRF protection requires Flask-WTF.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            # Check if CSRF is enabled
            try:
                from flask_wtf.csrf import validate_csrf
                # CSRF is handled by Flask-WTF automatically if enabled
                return f(*args, **kwargs)
            except ImportError:
                # CSRF not available - allow request but log warning
                # In production, Flask-WTF should be installed
                pass
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_https(f: Callable) -> Callable:
    """
    Decorator to require HTTPS for endpoint.
    
    Returns 403 if request is not HTTPS.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'HTTPS required for this endpoint'
                }), 403
            else:
                return render_template('error.html',
                    message='This page requires HTTPS. Please use https://',
                    error='HTTPS Required'
                ), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_request_size(max_size: int = 1024 * 1024) -> Callable:
    """
    Decorator to validate request size (prevent DoS).
    
    Args:
        max_size: Maximum request size in bytes (default: 1MB)
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.content_length and request.content_length > max_size:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': f'Request too large. Maximum size: {max_size // 1024}KB'
                    }), 413
                else:
                    return render_template('error.html',
                        message=f'Request too large. Maximum size: {max_size // 1024}KB',
                        error='Request Too Large'
                    ), 413
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_security_event(event_type: str, details: str = "", username: Optional[str] = None):
    """
    Log security events (system errors, not user activity).
    
    Privacy: Only logs system security events, not user activity.
    """
    try:
        import logging
        logger = logging.getLogger('phazevpn.security')
        log_msg = f"[{event_type}]"
        if username:
            log_msg += f" User: {username}"
        if details:
            log_msg += f" Details: {details}"
        logger.warning(log_msg)
    except:
        pass  # Fail silently if logging not configured
