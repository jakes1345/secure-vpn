"""
Centralized Configuration Management for SecureVPN Web Portal

This module provides a single source of truth for all configuration values,
using environment variables with sensible defaults.
"""

import os
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any


class Config:
    """Main configuration class for the application"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    WEB_PORTAL_DIR = Path(__file__).parent
    
    # VPN directory detection (try multiple locations)
    @staticmethod
    def get_vpn_dir() -> Path:
        """Detect VPN installation directory"""
        possible_paths = [
            Config.BASE_DIR,
            Path('/opt/phaze-vpn'),
            Path('/opt/secure-vpn'),
        ]
        
        for path in possible_paths:
            if (path / 'vpn-manager.py').exists():
                return path
        
        # Default to /opt/phaze-vpn for VPS installations
        return Path('/opt/phaze-vpn')
    
    VPN_DIR = get_vpn_dir()
    
    # File paths
    USERS_FILE = VPN_DIR / 'users.json'
    CLIENT_CONFIGS_DIR = VPN_DIR / 'client-configs'
    LOGS_DIR = VPN_DIR / 'logs'
    STATUS_LOG = LOGS_DIR / 'status.log'
    ACTIVITY_LOG = LOGS_DIR / 'activity.log'
    CONNECTION_HISTORY = LOGS_DIR / 'connection-history.json'
    PAYMENT_REQUESTS_FILE = LOGS_DIR / 'payment-requests.json'
    TICKETS_FILE = LOGS_DIR / 'tickets.json'
    
    # Flask configuration
    SECRET_KEY = os.environ.get(
        'FLASK_SECRET_KEY',
        'Y8Kp3mN9qR2vX7wL5zA6bC4dE1fG8hI0jK2lM6nO4pQ9rS3tU7vW1xY5zA8bC0dE2fG4hI6jK8lM0nO2pQ4rS6tU8vW0xY2zA4bC6dE8fG0hI2jK4lM6nO8pQ0rS2tU4vW6xY8zA0bC2dE4'
    )
    
    # Security settings
    IS_HTTPS = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = IS_HTTPS
    SESSION_COOKIE_NAME = '__Secure-VPN-Session' if IS_HTTPS else 'VPN-Session'
    SESSION_COOKIE_PATH = '/'
    SESSION_REFRESH_EACH_REQUEST = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # VPN server configuration
    VPN_SERVER_IP = os.environ.get('VPN_SERVER_IP', 'phazevpn.com')
    VPN_SERVER_PORT = int(os.environ.get('VPN_SERVER_PORT', '1194'))
    
    # Database configuration
    DB_CONFIG_FILE = WEB_PORTAL_DIR / 'db_config.json'
    
    # Email configuration
    EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER', 'mailgun')  # mailgun, mailjet, smtp, outlook
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', '')
    MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY', '')
    MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '')
    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # Payment configuration
    STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_MAX_REQUESTS = int(os.environ.get('RATE_LIMIT_MAX_REQUESTS', '100'))
    RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('RATE_LIMIT_WINDOW_SECONDS', '3600'))
    
    # CSRF Protection
    CSRF_ENABLED = os.environ.get('CSRF_ENABLED', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = LOGS_DIR / 'web-portal.log'
    
    # Feature flags
    ENABLE_2FA = os.environ.get('ENABLE_2FA', 'true').lower() == 'true'
    ENABLE_PAYMENTS = os.environ.get('ENABLE_PAYMENTS', 'true').lower() == 'true'
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', 'true').lower() == 'true'
    
    # Subscription tiers and limits
    SUBSCRIPTION_TIERS: Dict[str, Dict[str, Any]] = {
        'free': {
            'name': 'Free',
            'price': 0,
            'max_clients': 1,
            'max_connections': 1,
            'bandwidth_limit': None,  # No limit
            'features': ['Basic VPN', 'Ad Blocking'],
        },
        'basic': {
            'name': 'Basic',
            'price': 4.99,
            'max_clients': 3,
            'max_connections': 3,
            'bandwidth_limit': None,
            'features': ['Basic VPN', 'Ad Blocking', 'Email Support'],
        },
        'premium': {
            'name': 'Premium',
            'price': 9.99,
            'max_clients': 10,
            'max_connections': 10,
            'bandwidth_limit': None,
            'features': ['Premium VPN', 'Ad Blocking', 'Priority Support', 'Multiple Protocols'],
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 29.99,
            'max_clients': -1,  # Unlimited
            'max_connections': -1,  # Unlimited
            'bandwidth_limit': None,
            'features': ['Enterprise VPN', 'Dedicated Support', 'Custom Configuration', 'SLA'],
        },
    }
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': (
            'geolocation=(), microphone=(), camera=(), payment=(), '
            'usb=(), magnetometer=(), gyroscope=(), accelerometer=()'
        ),
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Resource-Policy': 'same-origin',
        'Server': '',  # Don't reveal server type
    }
    
    # Content Security Policy
    CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.VPN_DIR,
            cls.CLIENT_CONFIGS_DIR,
            cls.LOGS_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration and return True if valid"""
        errors = []
        
        # Check required paths
        if not cls.VPN_DIR.exists():
            errors.append(f"VPN directory not found: {cls.VPN_DIR}")
        
        # Check secret key
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY is using default value - change in production!")
        
        # Check database config
        if not cls.DB_CONFIG_FILE.exists():
            errors.append(f"Database config not found: {cls.DB_CONFIG_FILE}")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True


# Development configuration (for local testing)
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    IS_HTTPS = False


# Production configuration
class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    IS_HTTPS = True


# Testing configuration
class TestingConfig(Config):
    """Testing-specific configuration"""
    DEBUG = True
    TESTING = True
    SESSION_COOKIE_SECURE = False
    IS_HTTPS = False


# Configuration selector
def get_config(env: str = None) -> Config:
    """
    Get configuration based on environment
    
    Args:
        env: Environment name (development, production, testing)
             If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration object
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'production')
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    
    return configs.get(env.lower(), ProductionConfig)
