#!/usr/bin/env python3
"""
Error Messages Module
Provides consistent, user-friendly error messages throughout the application
"""

# User-friendly error messages
ERROR_MESSAGES = {
    # Authentication errors
    'INVALID_CREDENTIALS': 'Invalid username or password. Please check your credentials and try again.',
    'ACCOUNT_LOCKED': 'Your account has been temporarily locked due to too many failed login attempts. Please try again later.',
    'EMAIL_NOT_VERIFIED': 'Please verify your email address before logging in. Check your inbox for the verification link.',
    'SESSION_EXPIRED': 'Your session has expired. Please log in again.',
    'NOT_AUTHENTICATED': 'You must be logged in to access this page.',
    'ACCESS_DENIED': 'You do not have permission to access this resource.',
    
    # Validation errors
    'INVALID_USERNAME': 'Username must be 3-30 characters and contain only letters, numbers, underscores, and hyphens.',
    'INVALID_EMAIL': 'Please enter a valid email address.',
    'INVALID_PASSWORD': 'Password must be at least 8 characters and contain both letters and numbers.',
    'PASSWORDS_DONT_MATCH': 'Passwords do not match. Please try again.',
    'WEAK_PASSWORD': 'Password is too weak. Please choose a stronger password.',
    'EMAIL_IN_USE': 'This email address is already registered.',
    'USERNAME_EXISTS': 'This username is already taken. Please choose another.',
    
    # Client errors
    'CLIENT_NOT_FOUND': 'VPN client configuration not found.',
    'CLIENT_EXISTS': 'A client with this name already exists.',
    'CLIENT_LIMIT_REACHED': 'You have reached the maximum number of clients for your subscription tier.',
    'INVALID_CLIENT_NAME': 'Client name must be 1-50 characters and contain only letters, numbers, underscores, and hyphens.',
    
    # VPN errors
    'VPN_NOT_RUNNING': 'VPN server is not running. Please contact support.',
    'VPN_CONNECTION_FAILED': 'Failed to connect to VPN. Please check your configuration and try again.',
    'CONFIG_GENERATION_FAILED': 'Failed to generate VPN configuration. Please try again or contact support.',
    
    # Payment errors
    'PAYMENT_FAILED': 'Payment processing failed. Please check your payment method and try again.',
    'PAYMENT_NOT_FOUND': 'Payment record not found.',
    'INVALID_PAYMENT_AMOUNT': 'Invalid payment amount.',
    
    # Ticket errors
    'TICKET_NOT_FOUND': 'Support ticket not found.',
    'TICKET_ACCESS_DENIED': 'You do not have permission to access this ticket.',
    'MESSAGE_REQUIRED': 'Message is required.',
    'SUBJECT_REQUIRED': 'Subject is required.',
    
    # System errors
    'DATABASE_ERROR': 'A database error occurred. Please try again later.',
    'SERVER_ERROR': 'An internal server error occurred. Please try again later or contact support.',
    'RATE_LIMIT_EXCEEDED': 'Too many requests. Please wait a moment and try again.',
    'REQUEST_TOO_LARGE': 'Request is too large. Please reduce the size and try again.',
    
    # Generic
    'REQUIRED_FIELD': 'This field is required.',
    'INVALID_INPUT': 'Invalid input provided. Please check your data and try again.',
    'OPERATION_FAILED': 'Operation failed. Please try again.',
}

def get_error_message(error_key: str, default: str = None) -> str:
    """
    Get user-friendly error message by key.
    
    Args:
        error_key: Error message key
        default: Default message if key not found
        
    Returns:
        User-friendly error message
    """
    return ERROR_MESSAGES.get(error_key, default or 'An error occurred. Please try again.')

def format_error(error_key: str, **kwargs) -> str:
    """
    Format error message with variables.
    
    Args:
        error_key: Error message key
        **kwargs: Variables to format into message
        
    Returns:
        Formatted error message
    """
    message = get_error_message(error_key)
    try:
        return message.format(**kwargs)
    except:
        return message

# Success messages
SUCCESS_MESSAGES = {
    'LOGIN_SUCCESS': 'Successfully logged in!',
    'LOGOUT_SUCCESS': 'Successfully logged out.',
    'SIGNUP_SUCCESS': 'Account created successfully! Please check your email to verify your account.',
    'EMAIL_VERIFIED': 'Email address verified successfully!',
    'PASSWORD_CHANGED': 'Password changed successfully.',
    'PASSWORD_RESET_SENT': 'Password reset link sent to your email.',
    'PROFILE_UPDATED': 'Profile updated successfully.',
    'CLIENT_CREATED': 'VPN client created successfully.',
    'CLIENT_DELETED': 'VPN client deleted successfully.',
    'TICKET_CREATED': 'Support ticket created successfully.',
    'TICKET_REPLIED': 'Reply added successfully.',
    'PAYMENT_SUBMITTED': 'Payment submitted successfully.',
    'PAYMENT_APPROVED': 'Payment approved successfully.',
}

def get_success_message(success_key: str, default: str = None) -> str:
    """
    Get user-friendly success message by key.
    
    Args:
        success_key: Success message key
        default: Default message if key not found
        
    Returns:
        User-friendly success message
    """
    return SUCCESS_MESSAGES.get(success_key, default or 'Operation completed successfully.')
