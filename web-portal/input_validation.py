#!/usr/bin/env python3
"""
Input Validation Utilities
Provides secure input validation and sanitization for all user inputs
"""

import re
from typing import Optional, Tuple

# Maximum lengths
MAX_USERNAME_LENGTH = 30
MAX_EMAIL_LENGTH = 255
MAX_PASSWORD_LENGTH = 128
MAX_CLIENT_NAME_LENGTH = 50
MAX_MESSAGE_LENGTH = 5000
MAX_SUBJECT_LENGTH = 200

# Patterns
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
CLIENT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username
    
    Returns:
        (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Username must be no more than {MAX_USERNAME_LENGTH} characters"
    
    if not USERNAME_PATTERN.match(username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    # Reserved usernames
    reserved = ['admin', 'moderator', 'root', 'system', 'api', 'www', 'mail', 'ftp']
    if username.lower() in reserved:
        return False, "This username is reserved"
    
    return True, None

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address
    
    Returns:
        (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    email = email.strip().lower()
    
    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"Email must be no more than {MAX_EMAIL_LENGTH} characters"
    
    if not EMAIL_PATTERN.match(email):
        return False, "Please enter a valid email address"
    
    # Block disposable email domains (basic list)
    disposable_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
    domain = email.split('@')[1] if '@' in email else ''
    if domain in disposable_domains:
        return False, "Disposable email addresses are not allowed"
    
    return True, None

def validate_password(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength
    
    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be no more than {MAX_PASSWORD_LENGTH} characters"
    
    # Check for common weak passwords
    weak_passwords = ['password', '123456', '12345678', 'qwerty', 'abc123']
    if password.lower() in weak_passwords:
        return False, "Password is too weak. Please choose a stronger password"
    
    return True, None

def validate_client_name(client_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate client name
    
    Returns:
        (is_valid, error_message)
    """
    if not client_name:
        return False, "Client name is required"
    
    client_name = client_name.strip()
    
    if len(client_name) < 1:
        return False, "Client name cannot be empty"
    
    if len(client_name) > MAX_CLIENT_NAME_LENGTH:
        return False, f"Client name must be no more than {MAX_CLIENT_NAME_LENGTH} characters"
    
    if not CLIENT_NAME_PATTERN.match(client_name):
        return False, "Client name can only contain letters, numbers, underscores, and hyphens"
    
    return True, None

def sanitize_input(input_str: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
    """
    Sanitize user input
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum length (truncate if longer)
        allow_html: Whether to allow HTML (default: False, strips HTML)
    
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Strip whitespace
    sanitized = input_str.strip()
    
    # Remove HTML tags if not allowed
    if not allow_html:
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    # Truncate if too long
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def validate_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate message/contact form content
    
    Returns:
        (is_valid, error_message)
    """
    if not message:
        return False, "Message is required"
    
    message = message.strip()
    
    if len(message) < 10:
        return False, "Message must be at least 10 characters"
    
    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message must be no more than {MAX_MESSAGE_LENGTH} characters"
    
    return True, None

def validate_subject(subject: str) -> Tuple[bool, Optional[str]]:
    """
    Validate subject line
    
    Returns:
        (is_valid, error_message)
    """
    if not subject:
        return False, "Subject is required"
    
    subject = subject.strip()
    
    if len(subject) < 3:
        return False, "Subject must be at least 3 characters"
    
    if len(subject) > MAX_SUBJECT_LENGTH:
        return False, f"Subject must be no more than {MAX_SUBJECT_LENGTH} characters"
    
    return True, None

def validate_protocol(protocol: str) -> Tuple[bool, Optional[str]]:
    """
    Validate VPN protocol
    
    Returns:
        (is_valid, error_message)
    """
    valid_protocols = ['openvpn', 'wireguard', 'phazevpn']
    protocol = protocol.lower().strip()
    
    if protocol not in valid_protocols:
        return False, f"Protocol must be one of: {', '.join(valid_protocols)}"
    
    return True, None
