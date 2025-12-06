#!/usr/bin/env python3
"""
Email Templates System - Jinja2-based email templates
Provides reusable email templates with variables
"""

from pathlib import Path
from typing import Dict, Optional
import os

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("⚠️  Jinja2 not available. Install with: pip3 install jinja2")

# Template directory
TEMPLATE_DIR = Path(__file__).parent / 'templates' / 'emails'

def get_template_env():
    """Get Jinja2 template environment"""
    if not JINJA2_AVAILABLE:
        return None
    
    if not TEMPLATE_DIR.exists():
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True
    )

def render_email_template(template_name: str, variables: Dict, 
                         html: bool = True) -> Optional[str]:
    """
    Render email template with variables
    
    Args:
        template_name: Template filename (e.g., 'welcome.html')
        variables: Dictionary of template variables
        html: If True, render HTML template, else text template
    
    Returns:
        Rendered template string or None if error
    """
    if not JINJA2_AVAILABLE:
        return None
    
    env = get_template_env()
    if not env:
        return None
    
    # Determine template file extension
    extension = '.html' if html else '.txt'
    template_file = f"{template_name}{extension}"
    
    try:
        template = env.get_template(template_file)
        return template.render(**variables)
    except TemplateNotFound:
        print(f"⚠️  Template not found: {template_file}")
        return None
    except Exception as e:
        print(f"❌ Template rendering error: {e}")
        return None

def get_email_template(template_name: str, variables: Dict) -> tuple[Optional[str], Optional[str]]:
    """
    Get both HTML and text versions of email template
    
    Returns:
        (html_content, text_content)
    """
    html_content = render_email_template(template_name, variables, html=True)
    text_content = render_email_template(template_name, variables, html=False)
    
    return html_content, text_content

# Predefined template variables
DEFAULT_VARIABLES = {
    'site_name': 'PhazeVPN',
    'site_url': 'https://phazevpn.com',
    'support_email': 'support@phazevpn.com',
    'company_name': 'PhazeVPN',
    'logo_url': 'https://phazevpn.com/static/images/logo.png',
}

def render_with_defaults(template_name: str, variables: Dict) -> tuple[Optional[str], Optional[str]]:
    """Render template with default variables merged"""
    merged_vars = {**DEFAULT_VARIABLES, **variables}
    return get_email_template(template_name, merged_vars)
