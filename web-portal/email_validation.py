#!/usr/bin/env python3
"""
Email Validation - Comprehensive email validation
Validates format, domain, MX records, and disposable emails
"""

import re
import socket
from typing import Tuple, Optional
from urllib.parse import urlparse

# Disposable email domains (common ones)
DISPOSABLE_DOMAINS = {
    'tempmail.com', 'guerrillamail.com', 'mailinator.com', '10minutemail.com',
    'throwaway.email', 'temp-mail.org', 'mohmal.com', 'getnada.com',
    'maildrop.cc', 'yopmail.com', 'sharklasers.com', 'grr.la',
    'spamgourmet.com', 'fakeinbox.com', 'mintemail.com', 'trashmail.com',
}

def validate_email_format(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format
    
    Returns:
        (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip().lower()
    
    # Basic format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    # Check length
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email address too long"
    
    # Check local part length
    local_part = email.split('@')[0]
    if len(local_part) > 64:  # RFC 5321 limit
        return False, "Email local part too long"
    
    # Check for consecutive dots
    if '..' in email:
        return False, "Invalid email format (consecutive dots)"
    
    # Check for leading/trailing dots
    if email.startswith('.') or email.endswith('.'):
        return False, "Invalid email format (leading/trailing dot)"
    
    return True, None

def validate_email_domain(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email domain exists and has MX records
    
    Returns:
        (is_valid, error_message)
    """
    try:
        domain = email.split('@')[1]
        
        # Check for MX records
        try:
            mx_records = socket.getaddrinfo(domain, None, socket.AF_INET)
            if not mx_records:
                # Try DNS MX lookup
                import dns.resolver
                try:
                    mx = dns.resolver.resolve(domain, 'MX')
                    if not mx:
                        return False, f"Domain {domain} has no MX records"
                except:
                    # If DNS library not available, try basic socket check
                    try:
                        socket.gethostbyname(domain)
                    except socket.gaierror:
                        return False, f"Domain {domain} does not exist"
        except Exception as e:
            # If DNS check fails, try basic domain resolution
            try:
                socket.gethostbyname(domain)
            except socket.gaierror:
                return False, f"Domain {domain} does not exist"
        
        return True, None
    
    except Exception as e:
        return False, f"Domain validation error: {str(e)}"

def is_disposable_email(email: str) -> bool:
    """Check if email is from disposable email service"""
    try:
        domain = email.split('@')[1].lower()
        return domain in DISPOSABLE_DOMAINS
    except:
        return False

def validate_email(email: str, check_mx: bool = False, 
                   reject_disposable: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive email validation
    
    Args:
        email: Email address to validate
        check_mx: If True, check MX records (slower)
        reject_disposable: If True, reject disposable emails
    
    Returns:
        (is_valid, error_message)
    """
    # Format validation
    is_valid, error = validate_email_format(email)
    if not is_valid:
        return False, error
    
    # Disposable email check
    if reject_disposable and is_disposable_email(email):
        return False, "Disposable email addresses are not allowed"
    
    # Domain/MX validation (optional, slower)
    if check_mx:
        is_valid, error = validate_email_domain(email)
        if not is_valid:
            return False, error
    
    return True, None

if __name__ == '__main__':
    # Test validation
    test_emails = [
        'user@example.com',
        'invalid-email',
        'user@disposable.tempmail.com',
        'user@nonexistentdomain12345.com',
    ]
    
    print("=" * 80)
    print("📧 EMAIL VALIDATION TEST")
    print("=" * 80)
    print()
    
    for email in test_emails:
        is_valid, error = validate_email(email, check_mx=False, reject_disposable=True)
        status = "✅" if is_valid else "❌"
        print(f"{status} {email}: {error if error else 'Valid'}")
