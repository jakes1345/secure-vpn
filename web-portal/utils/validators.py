"""
Input validation utilities

This module wraps the existing input_validation.py for cleaner imports
"""

from input_validation import (
    validate_username as _validate_username,
    validate_email as _validate_email,
    validate_password as _validate_password,
    validate_client_name as _validate_client_name,
    validate_message as _validate_message,
    validate_subject as _validate_subject,
    validate_protocol as _validate_protocol,
    sanitize_input as _sanitize_input,
)

# Re-export with same interface
validate_username = _validate_username
validate_email = _validate_email
validate_password = _validate_password
validate_client_name = _validate_client_name
validate_message = _validate_message
validate_subject = _validate_subject
validate_protocol = _validate_protocol
sanitize_input = _sanitize_input

__all__ = [
    'validate_username',
    'validate_email',
    'validate_password',
    'validate_client_name',
    'validate_message',
    'validate_subject',
    'validate_protocol',
    'sanitize_input',
]
