"""
Payment Integrations for PhazeVPN
Supports: Stripe, Venmo, CashApp
"""

import os
import sys
import requests
import json
from datetime import datetime
from pathlib import Path

# Stripe Configuration
STRIPE_API_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Payment Settings File
PAYMENT_SETTINGS_FILE = Path(__file__).parent.parent / 'logs' / 'payment-settings.json'

def load_payment_settings():
    """Load payment settings"""
    if PAYMENT_SETTINGS_FILE.exists():
        try:
            with open(PAYMENT_SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Use settings file values if available
                return settings
        except:
            pass
    
    # Default settings - NO HARDCODED KEYS
    # All keys must come from environment variables for security
    return {
        'venmo_username': os.getenv('VENMO_USERNAME', '@jakes1328'),
        'cashapp_username': os.getenv('CASHAPP_USERNAME', '$jakes1328'),
        'cashapp_tag': os.getenv('CASHAPP_TAG', '$jakes1328'),
        'stripe_enabled': os.getenv('STRIPE_ENABLED', 'false').lower() == 'true',
        'stripe_secret_key': '',  # NEVER hardcode - use environment variable STRIPE_SECRET_KEY
        'stripe_publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY', ''),  # Can be public
        'stripe_webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET', '')
    }

def save_payment_settings(settings):
    """Save payment settings with file locking"""
    PAYMENT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Try to use file locking if available
        sys.path.insert(0, str(Path(__file__).parent))
        from file_locking import safe_json_write
        safe_json_write(PAYMENT_SETTINGS_FILE, settings, create_backup=True)
    except ImportError:
        # Fallback to regular write if file_locking not available
        with open(PAYMENT_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)

# ============================================
# STRIPE INTEGRATION
# ============================================

def create_stripe_checkout_session(amount, currency='usd', username=None, tier=None, success_url=None, cancel_url=None):
    """
    Create Stripe Checkout Session
    
    Args:
        amount: Amount in cents (e.g., 999 = $9.99)
        currency: Currency code (default: 'usd')
        username: Username for the subscription
        tier: Subscription tier name
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect after cancelled payment
    
    Returns:
        dict with session_id and url
    """
    # SECURITY: Only use environment variable, never hardcoded keys
    stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
    
    # Fallback to settings file ONLY if env var not set (for migration)
    if not stripe_key:
        settings = load_payment_settings()
        stripe_key = settings.get('stripe_secret_key', '')
    
    if not stripe_key:
        return {'error': 'Stripe secret key not configured. Please set STRIPE_SECRET_KEY environment variable.'}
    
    headers = {
        'Authorization': f'Bearer {stripe_key}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'mode': 'payment',
        'payment_method_types[]': 'card',
        'line_items[0][price_data][currency]': currency,
        'line_items[0][price_data][product_data][name]': f'PhazeVPN {tier or "Premium"} Subscription',
        'line_items[0][price_data][unit_amount]': amount,
        'line_items[0][quantity]': 1,
        'success_url': success_url or 'https://phazevpn.duckdns.org/payment/success?session_id={CHECKOUT_SESSION_ID}',
        'cancel_url': cancel_url or 'https://phazevpn.duckdns.org/payment/cancel',
    }
    
    if username:
        data['metadata[username]'] = username
        data['metadata[tier]'] = tier or 'premium'
    
    try:
        response = requests.post(
            'https://api.stripe.com/v1/checkout/sessions',
            headers=headers,
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            session_data = response.json()
            return {
                'success': True,
                'session_id': session_data.get('id'),
                'url': session_data.get('url')
            }
        else:
            return {
                'error': f'Stripe API error: {response.text}'
            }
    except Exception as e:
        return {
            'error': f'Failed to create Stripe session: {str(e)}'
        }

def verify_stripe_payment(session_id):
    """
    Verify Stripe payment by checking session
    
    Returns:
        dict with payment status and details
    """
    # SECURITY: Only use environment variable, never hardcoded keys
    stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
    
    # Fallback to settings file ONLY if env var not set (for migration)
    if not stripe_key:
        settings = load_payment_settings()
        stripe_key = settings.get('stripe_secret_key', '')
    
    if not stripe_key:
        return {'error': 'Stripe API key not configured. Please set STRIPE_SECRET_KEY environment variable.'}
    
    headers = {
        'Authorization': f'Bearer {stripe_key}',
    }
    
    try:
        response = requests.get(
            f'https://api.stripe.com/v1/checkout/sessions/{session_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            session = response.json()
            
            return {
                'success': True,
                'paid': session.get('payment_status') == 'paid',
                'amount_total': session.get('amount_total', 0) / 100,  # Convert from cents
                'currency': session.get('currency', 'usd'),
                'customer_email': session.get('customer_details', {}).get('email'),
                'username': session.get('metadata', {}).get('username'),
                'tier': session.get('metadata', {}).get('tier'),
                'payment_intent': session.get('payment_intent')
            }
        else:
            return {
                'error': f'Failed to verify payment: {response.text}'
            }
    except Exception as e:
        return {
            'error': f'Error verifying payment: {str(e)}'
        }

def handle_stripe_webhook(payload, signature):
    """
    Handle Stripe webhook events with proper signature verification
    
    SECURITY: Uses constant-time comparison to prevent timing attacks
    
    Returns:
        dict with event type and data
    """
    # SECURITY: Get webhook secret from environment first
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    # Fallback to settings file ONLY if env var not set (for migration)
    if not webhook_secret:
        settings = load_payment_settings()
        webhook_secret = settings.get('stripe_webhook_secret', '')
    
    if not webhook_secret:
        return {'error': 'Webhook secret not configured. Please set STRIPE_WEBHOOK_SECRET environment variable.'}
    
    try:
        import hmac
        import hashlib
        
        # SECURITY: Stripe sends signature in format "t=timestamp,v1=signature"
        # Extract the actual signature
        if ',' in signature:
            parts = signature.split(',')
            for part in parts:
                if part.startswith('v1='):
                    signature = part[3:]
                    break
        
        # Compute expected signature
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # SECURITY: Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, expected_signature):
            return {'error': 'Invalid webhook signature'}
        
        event = json.loads(payload)
        event_type = event.get('type')
        event_data = event.get('data', {}).get('object', {})
        
        return {
            'success': True,
            'type': event_type,
            'data': event_data
        }
    except Exception as e:
        return {
            'error': f'Error processing webhook: {str(e)}'
        }

# ============================================
# VENMO/CASHAPP (Manual Verification)
# ============================================

def create_manual_payment_request(username, amount, tier, payment_method='venmo'):
    """
    Create manual payment request for Venmo/CashApp
    
    Returns:
        dict with payment request details
    """
    settings = load_payment_settings()
    
    payment_info = {
        'venmo': {
            'username': settings.get('venmo_username', ''),
            'instructions': f'Send ${amount:.2f} to @{settings.get("venmo_username", "")} on Venmo'
        },
        'cashapp': {
            'username': settings.get('cashapp_username', ''),
            'tag': settings.get('cashapp_tag', ''),
            'instructions': f'Send ${amount:.2f} to ${settings.get("cashapp_username", "")} on CashApp'
        }
    }
    
    info = payment_info.get(payment_method.lower(), payment_info['venmo'])
    
    return {
        'success': True,
        'payment_method': payment_method,
        'amount': amount,
        'tier': tier,
        'username': username,
        'instructions': info.get('instructions', ''),
        'recipient': info.get('username') or info.get('tag', ''),
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }

def verify_manual_payment(transaction_id, payment_method='venmo'):
    """
    Verify manual payment (Venmo/CashApp)
    
    Note: This requires manual verification by admin
    For automated verification, you'd need to use their APIs
    which may not be publicly available
    
    Returns:
        dict with verification status
    """
    # Manual verification - admin must check
    return {
        'success': False,
        'message': 'Manual payment requires admin verification. Please submit transaction ID for review.'
    }

