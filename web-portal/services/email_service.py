"""
Email Service - Unified interface for sending emails

This service consolidates all email providers (Mailgun, Mailjet, SMTP, Outlook)
into a single, easy-to-use interface with automatic fallback support.
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import email modules
try:
    from email_api import send_email_mailgun
except ImportError:
    send_email_mailgun = None

try:
    from email_mailjet import send_email_mailjet
except ImportError:
    send_email_mailjet = None

try:
    from email_smtp import send_email_smtp
except ImportError:
    send_email_smtp = None

try:
    from email_outlook_oauth2 import send_email_outlook
except ImportError:
    send_email_outlook = None

try:
    from email_templates import (
        get_welcome_email_html,
        get_verification_email_html,
        get_password_reset_email_html,
        get_payment_confirmation_email_html,
    )
except ImportError:
    # Fallback templates
    def get_welcome_email_html(username: str, **kwargs) -> str:
        return f"<html><body><h1>Welcome {username}!</h1></body></html>"
    
    def get_verification_email_html(username: str, verification_link: str, **kwargs) -> str:
        return f"<html><body><h1>Verify your email</h1><a href='{verification_link}'>Click here</a></body></html>"
    
    def get_password_reset_email_html(username: str, reset_link: str, **kwargs) -> str:
        return f"<html><body><h1>Reset your password</h1><a href='{reset_link}'>Click here</a></body></html>"
    
    def get_payment_confirmation_email_html(username: str, amount: float, **kwargs) -> str:
        return f"<html><body><h1>Payment Confirmed</h1><p>Amount: ${amount}</p></body></html>"


logger = logging.getLogger(__name__)


class EmailService:
    """
    Unified email service with multiple provider support and automatic fallback
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize email service
        
        Args:
            config: Configuration dictionary with email provider settings
        """
        self.config = config or {}
        self.provider = self.config.get('provider', 'mailgun')
        
        # Provider priority order for fallback
        self.providers = ['mailgun', 'mailjet', 'smtp', 'outlook']
        
        # Track which providers are available
        self.available_providers = {
            'mailgun': send_email_mailgun is not None,
            'mailjet': send_email_mailjet is not None,
            'smtp': send_email_smtp is not None,
            'outlook': send_email_outlook is not None,
        }
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Send an email using configured provider with automatic fallback
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional)
            attachments: List of attachments (optional)
            use_fallback: Whether to try fallback providers on failure
        
        Returns:
            Dictionary with 'success' boolean and 'message' or 'error'
        """
        # Try primary provider first
        result = self._send_with_provider(
            self.provider,
            to_email,
            subject,
            html_body,
            from_email,
            from_name,
            attachments,
        )
        
        if result['success']:
            return result
        
        # Try fallback providers if enabled
        if use_fallback:
            logger.warning(f"Primary provider {self.provider} failed, trying fallbacks")
            
            for provider in self.providers:
                if provider == self.provider:
                    continue  # Skip primary provider
                
                if not self.available_providers.get(provider):
                    continue  # Skip unavailable providers
                
                logger.info(f"Trying fallback provider: {provider}")
                result = self._send_with_provider(
                    provider,
                    to_email,
                    subject,
                    html_body,
                    from_email,
                    from_name,
                    attachments,
                )
                
                if result['success']:
                    logger.info(f"Successfully sent email using fallback provider: {provider}")
                    return result
        
        # All providers failed
        return {
            'success': False,
            'error': 'All email providers failed',
        }
    
    def _send_with_provider(
        self,
        provider: str,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: Optional[str],
        from_name: Optional[str],
        attachments: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Send email with specific provider
        
        Returns:
            Dictionary with 'success' boolean and 'message' or 'error'
        """
        try:
            if provider == 'mailgun' and send_email_mailgun:
                return send_email_mailgun(
                    to_email=to_email,
                    subject=subject,
                    html_body=html_body,
                    from_email=from_email,
                    from_name=from_name,
                )
            
            elif provider == 'mailjet' and send_email_mailjet:
                return send_email_mailjet(
                    to_email=to_email,
                    subject=subject,
                    html_body=html_body,
                    from_email=from_email,
                    from_name=from_name,
                )
            
            elif provider == 'smtp' and send_email_smtp:
                return send_email_smtp(
                    to_email=to_email,
                    subject=subject,
                    html_body=html_body,
                    from_email=from_email,
                    from_name=from_name,
                )
            
            elif provider == 'outlook' and send_email_outlook:
                return send_email_outlook(
                    to_email=to_email,
                    subject=subject,
                    html_body=html_body,
                )
            
            else:
                return {
                    'success': False,
                    'error': f'Provider {provider} not available',
                }
        
        except Exception as e:
            logger.error(f"Error sending email with {provider}: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def send_welcome_email(self, username: str, email: str) -> Dict[str, Any]:
        """
        Send welcome email to new user
        
        Args:
            username: Username
            email: User's email address
        
        Returns:
            Result dictionary
        """
        subject = "Welcome to SecureVPN!"
        html_body = get_welcome_email_html(username)
        
        return self.send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
        )
    
    def send_verification_email(
        self,
        username: str,
        email: str,
        verification_link: str,
    ) -> Dict[str, Any]:
        """
        Send email verification link
        
        Args:
            username: Username
            email: User's email address
            verification_link: Verification URL
        
        Returns:
            Result dictionary
        """
        subject = "Verify your SecureVPN account"
        html_body = get_verification_email_html(username, verification_link)
        
        return self.send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
        )
    
    def send_password_reset_email(
        self,
        username: str,
        email: str,
        reset_link: str,
    ) -> Dict[str, Any]:
        """
        Send password reset link
        
        Args:
            username: Username
            email: User's email address
            reset_link: Password reset URL
        
        Returns:
            Result dictionary
        """
        subject = "Reset your SecureVPN password"
        html_body = get_password_reset_email_html(username, reset_link)
        
        return self.send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
        )
    
    def send_payment_confirmation_email(
        self,
        username: str,
        email: str,
        amount: float,
        subscription_tier: str,
    ) -> Dict[str, Any]:
        """
        Send payment confirmation email
        
        Args:
            username: Username
            email: User's email address
            amount: Payment amount
            subscription_tier: Subscription tier name
        
        Returns:
            Result dictionary
        """
        subject = "Payment Confirmation - SecureVPN"
        html_body = get_payment_confirmation_email_html(
            username,
            amount,
            subscription_tier=subscription_tier,
        )
        
        return self.send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
        )


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service(config: Optional[Dict[str, Any]] = None) -> EmailService:
    """
    Get or create email service instance
    
    Args:
        config: Configuration dictionary (optional)
    
    Returns:
        EmailService instance
    """
    global _email_service
    
    if _email_service is None:
        _email_service = EmailService(config)
    
    return _email_service


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function to send email using global service
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_body: HTML body
        **kwargs: Additional arguments passed to EmailService.send_email
    
    Returns:
        Result dictionary
    """
    service = get_email_service()
    return service.send_email(to_email, subject, html_body, **kwargs)
