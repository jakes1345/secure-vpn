"""
Secure Authentication System
Super secure password hashing, sessions, 2FA, rate limiting
"""

import bcrypt
import jwt
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, jsonify
import pyotp
import qrcode
from io import BytesIO
import base64

# Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # Generate random secret
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
BCRYPT_ROUNDS = 12

# Rate limiting storage (in production, use Redis)
login_attempts = {}
rate_limit_window = 900  # 15 minutes in seconds
max_login_attempts = 5
account_lockout_time = 3600  # 1 hour

class SecureAuth:
    """Super secure authentication system"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def generate_jwt_token(user_id: str, username: str) -> str:
        """Generate secure JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)  # Unique token ID
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_jwt_token(token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def check_rate_limit(identifier: str) -> tuple[bool, int]:
        """
        Check rate limiting
        Returns: (allowed, remaining_attempts)
        """
        now = time.time()
        key = f"login_{identifier}"
        
        if key not in login_attempts:
            login_attempts[key] = {'count': 0, 'reset_time': now + rate_limit_window}
            return True, max_login_attempts
        
        attempts = login_attempts[key]
        
        # Reset if window expired
        if now > attempts['reset_time']:
            attempts['count'] = 0
            attempts['reset_time'] = now + rate_limit_window
            return True, max_login_attempts
        
        # Check if exceeded
        if attempts['count'] >= max_login_attempts:
            return False, 0
        
        return True, max_login_attempts - attempts['count']
    
    @staticmethod
    def record_login_attempt(identifier: str, success: bool):
        """Record login attempt"""
        key = f"login_{identifier}"
        now = time.time()
        
        if key not in login_attempts:
            login_attempts[key] = {'count': 0, 'reset_time': now + rate_limit_window}
        
        if not success:
            login_attempts[key]['count'] += 1
    
    @staticmethod
    def check_account_lockout(user_id: str) -> tuple[bool, int]:
        """
        Check if account is locked out
        Returns: (is_locked, unlock_time)
        """
        key = f"lockout_{user_id}"
        if key not in login_attempts:
            return False, 0
        
        lockout = login_attempts[key]
        now = time.time()
        
        if now < lockout['unlock_time']:
            remaining = int(lockout['unlock_time'] - now)
            return True, remaining
        
        # Lockout expired
        del login_attempts[key]
        return False, 0
    
    @staticmethod
    def lock_account(user_id: str):
        """Lock account after too many failed attempts"""
        key = f"lockout_{user_id}"
        login_attempts[key] = {
            'unlock_time': time.time() + account_lockout_time
        }
    
    @staticmethod
    def generate_2fa_secret() -> str:
        """Generate 2FA secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def verify_2fa(secret: str, token: str) -> bool:
        """Verify 2FA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_2fa_qr(username: str, secret: str, issuer: str = "PhazeVPN") -> str:
        """Generate QR code for 2FA setup"""
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{img_base64}"


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = SecureAuth.verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user_id = payload['user_id']
        request.username = payload['username']
        
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        # Check if user is admin (implement based on your user model)
        # For now, placeholder
        if not hasattr(request, 'is_admin') or not request.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_login(f):
    """Decorator for rate limiting login attempts"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        identifier = request.remote_addr
        
        # Check rate limit
        allowed, remaining = SecureAuth.check_rate_limit(identifier)
        if not allowed:
            return jsonify({
                'error': 'Too many login attempts. Please try again later.',
                'retry_after': int(rate_limit_window)
            }), 429
        
        response = f(*args, **kwargs)
        
        # Record attempt
        success = response[1] == 200 if isinstance(response, tuple) else False
        SecureAuth.record_login_attempt(identifier, success)
        
        # Add remaining attempts to response
        if isinstance(response, tuple) and len(response) > 1:
            headers = response[2] if len(response) > 2 else {}
            headers['X-RateLimit-Remaining'] = str(remaining - 1)
            return (response[0], response[1], headers)
        
        return response
    return decorated_function

