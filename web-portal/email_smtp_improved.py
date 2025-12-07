"""
Improved SMTP Email Module

This module provides a cleaner, more maintainable SMTP email implementation
with better error handling, logging, and configuration management.
"""

import smtplib
import logging
import secrets
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from typing import Optional, Tuple, Dict, Any
import os
import re

logger = logging.getLogger(__name__)


class SMTPEmailConfig:
    """SMTP Configuration"""
    
    def __init__(self):
        # Try to load from config file first
        try:
            from smtp_config import (
                SMTP_HOST as CFG_HOST,
                SMTP_PORT as CFG_PORT,
                SMTP_USER as CFG_USER,
                SMTP_PASSWORD as CFG_PASSWORD,
                FROM_EMAIL as CFG_FROM,
                FROM_NAME as CFG_NAME
            )
            self.host = CFG_HOST
            self.port = CFG_PORT
            self.user = CFG_USER
            self.password = CFG_PASSWORD
            self.from_email = CFG_FROM or CFG_USER
            self.from_name = CFG_NAME
        except ImportError:
            # Fallback to environment variables
            self.host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
            self.port = int(os.environ.get('SMTP_PORT', '587'))
            self.user = os.environ.get('SMTP_USER', '')
            self.password = os.environ.get('SMTP_PASSWORD', '')
            self.from_email = os.environ.get('FROM_EMAIL', self.user)
            self.from_name = os.environ.get('FROM_NAME', 'PhazeVPN')
        
        self.use_tls = True  # Always use TLS for security
        self.timeout = 30  # Connection timeout in seconds
    
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(self.user and self.password and self.host)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate SMTP configuration
        
        Returns:
            (is_valid, error_message)
        """
        if not self.user:
            return False, "SMTP_USER not set"
        
        if not self.password:
            return False, "SMTP_PASSWORD not set"
        
        if not self.host:
            return False, "SMTP_HOST not set"
        
        if not (1 <= self.port <= 65535):
            return False, f"Invalid SMTP_PORT: {self.port}"
        
        return True, None


class SMTPEmailSender:
    """SMTP Email Sender with improved error handling"""
    
    def __init__(self, config: Optional[SMTPEmailConfig] = None):
        """
        Initialize SMTP email sender
        
        Args:
            config: SMTP configuration (creates default if None)
        """
        self.config = config or SMTPEmailConfig()
    
    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML to plain text
        
        Args:
            html: HTML content
        
        Returns:
            Plain text version
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> MIMEMultipart:
        """
        Create email message with proper headers
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content (auto-generated if None)
        
        Returns:
            MIME message
        """
        msg = MIMEMultipart('alternative')
        
        # Set headers
        msg['Subject'] = subject
        msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
        msg['To'] = to_email
        msg['Reply-To'] = self.config.from_email
        msg['List-Unsubscribe'] = f"<mailto:{self.config.from_email}?subject=unsubscribe>"
        msg['X-Mailer'] = 'PhazeVPN'
        msg['X-Priority'] = '3'  # Normal priority
        msg['Message-ID'] = f"<{secrets.token_hex(16)}@phazevpn.com>"
        msg['Date'] = formatdate(localtime=True)
        msg['MIME-Version'] = '1.0'
        
        # Add text version (always include for better deliverability)
        if text_content is None:
            text_content = self._html_to_text(html_content)
        
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        
        # Add HTML version
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        return msg
    
    def send(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        retries: int = 3,
    ) -> Tuple[bool, str]:
        """
        Send email via SMTP with retry logic
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text version (auto-generated if None)
            retries: Number of retry attempts
        
        Returns:
            (success, message)
        """
        # Validate configuration
        is_valid, error = self.config.validate()
        if not is_valid:
            logger.error(f"SMTP configuration error: {error}")
            return False, f"SMTP configuration error: {error}"
        
        if not to_email:
            return False, "No recipient email provided"
        
        # Create message
        try:
            msg = self._create_message(to_email, subject, html_content, text_content)
        except Exception as e:
            logger.error(f"Error creating email message: {e}")
            return False, f"Error creating message: {e}"
        
        # Retry logic
        last_error = None
        for attempt in range(retries):
            try:
                # Create SSL context
                context = ssl.create_default_context()
                
                # Connect to SMTP server
                with smtplib.SMTP(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout
                ) as server:
                    # Enable debug output in development
                    if os.environ.get('DEBUG_SMTP'):
                        server.set_debuglevel(1)
                    
                    # Start TLS encryption
                    if self.config.use_tls:
                        server.starttls(context=context)
                    
                    # Login
                    server.login(self.config.user, self.config.password)
                    
                    # Send email
                    server.send_message(msg)
                    
                    logger.info(f"Email sent successfully to {to_email}")
                    return True, "Email sent successfully"
            
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"SMTP authentication failed: {e}"
                logger.error(error_msg)
                return False, error_msg  # Don't retry auth errors
            
            except smtplib.SMTPRecipientsRefused as e:
                error_msg = f"Recipient refused: {e}"
                logger.error(error_msg)
                return False, error_msg  # Don't retry invalid recipients
            
            except smtplib.SMTPException as e:
                last_error = f"SMTP error: {e}"
                logger.warning(f"Attempt {attempt + 1}/{retries} failed: {last_error}")
                if attempt < retries - 1:
                    continue  # Retry
            
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.warning(f"Attempt {attempt + 1}/{retries} failed: {last_error}")
                if attempt < retries - 1:
                    continue  # Retry
        
        # All retries failed
        error_msg = f"Failed to send email after {retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        return False, error_msg


# Global sender instance
_smtp_sender: Optional[SMTPEmailSender] = None


def get_smtp_sender(config: Optional[SMTPEmailConfig] = None) -> SMTPEmailSender:
    """
    Get or create SMTP sender instance
    
    Args:
        config: SMTP configuration (optional)
    
    Returns:
        SMTPEmailSender instance
    """
    global _smtp_sender
    
    if _smtp_sender is None:
        _smtp_sender = SMTPEmailSender(config)
    
    return _smtp_sender


def send_email_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to send email via SMTP
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text body (optional)
        from_email: Sender email (optional, uses config default)
        from_name: Sender name (optional, uses config default)
    
    Returns:
        Dictionary with 'success' boolean and 'message' or 'error'
    """
    sender = get_smtp_sender()
    
    # Override config if provided
    if from_email:
        sender.config.from_email = from_email
    if from_name:
        sender.config.from_name = from_name
    
    success, message = sender.send(to_email, subject, html_body, text_body)
    
    return {
        'success': success,
        'message' if success else 'error': message,
    }


# Backward compatibility with old interface
def send_email(to_email, subject, html_content, text_content=None, retries=3):
    """
    Legacy interface for backward compatibility
    
    Returns:
        (success: bool, message: str)
    """
    sender = get_smtp_sender()
    return sender.send(to_email, subject, html_content, text_content, retries)
