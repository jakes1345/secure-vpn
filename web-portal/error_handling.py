"""
Comprehensive Error Handling Module

Provides custom exceptions, error handlers, and utilities for
consistent error handling across the application.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


# ============================================
# Custom Exceptions
# ============================================

class VPNError(Exception):
    """Base exception for VPN-related errors"""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code or 'VPN_ERROR'
        super().__init__(self.message)


class AuthenticationError(VPNError):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 'AUTH_ERROR')


class AuthorizationError(VPNError):
    """User not authorized for this action"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, 'AUTHZ_ERROR')


class ValidationError(VPNError):
    """Input validation failed"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, 'VALIDATION_ERROR')
        self.field = field


class DatabaseError(VPNError):
    """Database operation failed"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message, 'DB_ERROR')


class EmailError(VPNError):
    """Email sending failed"""
    def __init__(self, message: str = "Failed to send email"):
        super().__init__(message, 'EMAIL_ERROR')


class PaymentError(VPNError):
    """Payment processing failed"""
    def __init__(self, message: str = "Payment failed"):
        super().__init__(message, 'PAYMENT_ERROR')


class RateLimitError(VPNError):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 'RATE_LIMIT_ERROR')


class ConfigurationError(VPNError):
    """Configuration error"""
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, 'CONFIG_ERROR')


class ClientError(VPNError):
    """VPN client operation failed"""
    def __init__(self, message: str = "Client operation failed"):
        super().__init__(message, 'CLIENT_ERROR')


# ============================================
# Error Response Builders
# ============================================

def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Build standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Application-specific error code
        details: Additional error details
    
    Returns:
        (response_dict, status_code)
    """
    response = {
        'success': False,
        'error': message,
    }
    
    if error_code:
        response['error_code'] = error_code
    
    if details:
        response['details'] = details
    
    return response, status_code


def validation_error_response(
    message: str,
    field: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Build validation error response
    
    Args:
        message: Error message
        field: Field that failed validation
    
    Returns:
        (response_dict, status_code)
    """
    details = {'field': field} if field else None
    return error_response(
        message,
        status_code=400,
        error_code='VALIDATION_ERROR',
        details=details,
    )


def auth_error_response(
    message: str = "Authentication required",
) -> Tuple[Dict[str, Any], int]:
    """
    Build authentication error response
    
    Args:
        message: Error message
    
    Returns:
        (response_dict, status_code)
    """
    return error_response(
        message,
        status_code=401,
        error_code='AUTH_ERROR',
    )


def forbidden_error_response(
    message: str = "Access forbidden",
) -> Tuple[Dict[str, Any], int]:
    """
    Build authorization error response
    
    Args:
        message: Error message
    
    Returns:
        (response_dict, status_code)
    """
    return error_response(
        message,
        status_code=403,
        error_code='AUTHZ_ERROR',
    )


def not_found_error_response(
    message: str = "Resource not found",
) -> Tuple[Dict[str, Any], int]:
    """
    Build not found error response
    
    Args:
        message: Error message
    
    Returns:
        (response_dict, status_code)
    """
    return error_response(
        message,
        status_code=404,
        error_code='NOT_FOUND',
    )


def server_error_response(
    message: str = "Internal server error",
) -> Tuple[Dict[str, Any], int]:
    """
    Build server error response
    
    Args:
        message: Error message
    
    Returns:
        (response_dict, status_code)
    """
    return error_response(
        message,
        status_code=500,
        error_code='SERVER_ERROR',
    )


# ============================================
# Flask Error Handlers
# ============================================

def register_error_handlers(app):
    """
    Register error handlers with Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        logger.warning(f"Validation error: {error.message}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(validation_error_response(
                error.message,
                getattr(error, 'field', None),
            )[0]), 400
        
        return render_template(
            'error.html',
            error_title='Validation Error',
            error_message=error.message,
        ), 400
    
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(error):
        """Handle authentication errors"""
        logger.warning(f"Authentication error: {error.message}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(auth_error_response(error.message)[0]), 401
        
        return render_template(
            'error.html',
            error_title='Authentication Required',
            error_message=error.message,
        ), 401
    
    @app.errorhandler(AuthorizationError)
    def handle_authz_error(error):
        """Handle authorization errors"""
        logger.warning(f"Authorization error: {error.message}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(forbidden_error_response(error.message)[0]), 403
        
        return render_template(
            'error.html',
            error_title='Access Forbidden',
            error_message=error.message,
        ), 403
    
    @app.errorhandler(DatabaseError)
    def handle_db_error(error):
        """Handle database errors"""
        logger.error(f"Database error: {error.message}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(server_error_response("Database error occurred")[0]), 500
        
        return render_template(
            'error.html',
            error_title='Database Error',
            error_message='A database error occurred. Please try again later.',
        ), 500
    
    @app.errorhandler(EmailError)
    def handle_email_error(error):
        """Handle email errors"""
        logger.error(f"Email error: {error.message}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(server_error_response("Failed to send email")[0]), 500
        
        return render_template(
            'error.html',
            error_title='Email Error',
            error_message='Failed to send email. Please try again later.',
        ), 500
    
    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error):
        """Handle rate limit errors"""
        logger.warning(f"Rate limit exceeded: {error.message}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(error_response(
                error.message,
                status_code=429,
                error_code='RATE_LIMIT_ERROR',
            )[0]), 429
        
        return render_template(
            'error.html',
            error_title='Rate Limit Exceeded',
            error_message=error.message,
        ), 429
    
    @app.errorhandler(404)
    def handle_404(error):
        """Handle 404 errors"""
        logger.info(f"404 error: {request.path}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(not_found_error_response()[0]), 404
        
        return render_template(
            'error.html',
            error_title='Page Not Found',
            error_message='The page you are looking for does not exist.',
        ), 404
    
    @app.errorhandler(500)
    def handle_500(error):
        """Handle 500 errors"""
        logger.error(f"500 error: {error}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(server_error_response()[0]), 500
        
        return render_template(
            'error.html',
            error_title='Internal Server Error',
            error_message='An internal server error occurred. Please try again later.',
        ), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors"""
        logger.exception(f"Unexpected error: {error}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(server_error_response()[0]), 500
        
        return render_template(
            'error.html',
            error_title='Unexpected Error',
            error_message='An unexpected error occurred. Please try again later.',
        ), 500


# ============================================
# Context Managers for Error Handling
# ============================================

class safe_operation:
    """
    Context manager for safe operations with automatic error handling
    
    Usage:
        with safe_operation("Creating user"):
            create_user(username, password)
    """
    
    def __init__(
        self,
        operation_name: str,
        raise_on_error: bool = True,
        log_errors: bool = True,
    ):
        """
        Initialize safe operation context
        
        Args:
            operation_name: Name of operation for logging
            raise_on_error: Whether to re-raise exceptions
            log_errors: Whether to log errors
        """
        self.operation_name = operation_name
        self.raise_on_error = raise_on_error
        self.log_errors = log_errors
        self.error = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            
            if self.log_errors:
                logger.error(
                    f"Error in {self.operation_name}: {exc_val}",
                    exc_info=True,
                )
            
            if not self.raise_on_error:
                return True  # Suppress exception
        
        return False  # Propagate exception if raise_on_error=True
