"""
Route decorators for authentication and authorization
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request
from typing import Callable, Any


def login_required(f: Callable) -> Callable:
    """
    Decorator to require login for a route
    
    Usage:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            return render_template('dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """
    Decorator to require admin role for a route
    
    Usage:
        @app.route('/admin')
        @admin_required
        def admin_panel():
            return render_template('admin.html')
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        if session.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def moderator_required(f: Callable) -> Callable:
    """
    Decorator to require moderator or admin role for a route
    
    Usage:
        @app.route('/moderate')
        @moderator_required
        def moderate():
            return render_template('moderate.html')
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        role = session.get('role', 'user')
        if role not in ['admin', 'moderator']:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def api_key_required(f: Callable) -> Callable:
    """
    Decorator to require API key for API routes
    
    Usage:
        @app.route('/api/data')
        @api_key_required
        def api_data():
            return jsonify({'data': 'value'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Check for API key in header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return {'error': 'API key required'}, 401
        
        # TODO: Validate API key against database
        # For now, just check if it exists
        if not api_key:
            return {'error': 'Invalid API key'}, 403
        
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(max_requests: int = 100, window_seconds: int = 3600):
    """
    Decorator to rate limit a route
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    
    Usage:
        @app.route('/api/endpoint')
        @rate_limit(max_requests=10, window_seconds=60)
        def api_endpoint():
            return jsonify({'status': 'ok'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # TODO: Implement rate limiting logic
            # This would check request count from IP/user in time window
            return f(*args, **kwargs)
        return decorated_function
    return decorator
