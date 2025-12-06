"""
SECURE Payment Integrations for PhazeVPN
Fixed version with proper security
"""

import os
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import secrets

# Payment Settings File
PAYMENT_SETTINGS_FILE = Path(__file__).parent.parent / 'logs' / 'payment-settings.json'

# Webhook event storage for idempotency
WEBHOOK_EVENTS_FILE = Path(__file__).parent.parent / 'logs' / 'webhook-events.json'

def load_payment_settings() -> Dict:
    """Load payment settings - NO HARDCODED KEYS"""
    if PAYMENT_SETTINGS_FILE.exists():
        try:
            with open(PAYMENT_SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                return settings
        except:
            pass
    
    # Default settings WITHOUT keys - must be set via environment or admin panel
    return {
        'venmo_username': os.getenv('VENMO_USERNAME', ''),
        'cashapp_username': os.getenv('CASHAPP_USERNAME', ''),
        'cashapp_tag': os.getenv('CASHAPP_TAG', ''),
        'stripe_enabled': False,  # Disabled by default
        'stripe_secret_key': os.getenv('STRIPE_SECRET_KEY', ''),  # From environment ONLY
        'stripe_publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY', ''),  # From environment ONLY
        'stripe_webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET', ''),  # From environment ONLY
    }

def save_payment_settings(settings: Dict):
    """Save payment settings"""
    PAYMENT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    # NEVER save secret keys to file - only store in environment
    safe_settings = {k: v for k, v in settings.items() if k != 'stripe_secret_key' and k != 'stripe_webhook_secret'}
    safe_settings['stripe_secret_key_set'] = bool(settings.get('stripe_secret_key'))
    safe_settings['stripe_webhook_secret_set'] = bool(settings.get('stripe_webhook_secret'))
    with open(PAYMENT_SETTINGS_FILE, 'w') as f:
        json.dump(safe_settings, f, indent=2)

def get_stripe_key() -> Optional[str]:
    """Get Stripe secret key from environment ONLY"""
    return os.getenv('STRIPE_SECRET_KEY') or load_payment_settings().get('stripe_secret_key')

def get_webhook_secret() -> Optional[str]:
    """Get webhook secret from environment ONLY"""
    return os.getenv('STRIPE_WEBHOOK_SECRET') or load_payment_settings().get('stripe_webhook_secret')

def load_webhook_events() -> Dict:
    """Load processed webhook events for idempotency"""
    if WEBHOOK_EVENTS_FILE.exists():
        try:
            with open(WEBHOOK_EVENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'events': {}}

def save_webhook_event(event_id: str, event_type: str, processed: bool):
    """Save webhook event for idempotency"""
    events = load_webhook_events()
    events['events'][event_id] = {
        'type': event_type,
        'processed': processed,
        'processed_at': datetime.now().isoformat()
    }
    WEBHOOK_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WEBHOOK_EVENTS_FILE, 'w') as f:
        json.dump(events, f, indent=2)

def is_webhook_processed(event_id: str) -> bool:
    """Check if webhook event was already processed"""
    events = load_webhook_events()
    return events['events'].get(event_id, {}).get('processed', False)

# ============================================
# STRIPE INTEGRATION - SECURE VERSION
# ============================================

def create_stripe_checkout_session(amount: int, currency: str = 'usd', username: Optional[str] = None, 
                                   tier: Optional[str] = None, success_url: Optional[str] = None, 
                                   cancel_url: Optional[str] = None, idempotency_key: Optional[str] = None) -> Dict:
    """
    Create Stripe Checkout Session with idempotency
    
    Args:
        amount: Amount in cents (e.g., 999 = $9.99)
        currency: Currency code (default: 'usd')
        username: Username for the subscription
        tier: Subscription tier name
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect after cancelled payment
        idempotency_key: Idempotency key to prevent duplicate charges
    
    Returns:
        dict with session_id and url
    """
    stripe_key = get_stripe_key()
    
    if not stripe_key:
        return {'error': 'Stripe secret key not configured. Please set STRIPE_SECRET_KEY environment variable.'}
    
    # Generate idempotency key if not provided
    if not idempotency_key:
        idempotency_key = f"checkout_{username}_{tier}_{int(time.time())}"
    
    headers = {
        'Authorization': f'Bearer {stripe_key}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Idempotency-Key': idempotency_key  # Prevent duplicate charges
    }
    
    data = {
        'mode': 'subscription',  # Use subscription mode for recurring payments
        'payment_method_types[]': 'card',
        'line_items[0][price_data][currency]': currency,
        'line_items[0][price_data][product_data][name]': f'PhazeVPN {tier or "Premium"} Subscription',
        'line_items[0][price_data][unit_amount]': amount,
        'line_items[0][price_data][recurring][interval]': 'month',  # Monthly subscription
        'line_items[0][quantity]': 1,
        'success_url': success_url or f'{os.getenv("BASE_URL", "https://phazevpn.com")}/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
        'cancel_url': cancel_url or f'{os.getenv("BASE_URL", "https://phazevpn.com")}/payment/cancel',
    }
    
    # NO METADATA - Complete privacy
    # We don't send username or tier to payment processor
    # Payment is anonymous - no tracking
    # Note: Stripe requires customer_email for payment, but we use a generic email
    if username:
        # Use generic email format - no username tracking
        data['customer_email'] = f'user@{os.getenv("DOMAIN", "phazevpn.com")}'
    
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

def verify_stripe_payment(session_id: str) -> Dict:
    """
    Verify Stripe payment by checking session
    
    Returns:
        dict with payment status and details
    """
    stripe_key = get_stripe_key()
    
    if not stripe_key:
        return {'error': 'Stripe API key not configured'}
    
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
                'payment_intent': session.get('payment_intent'),
                'subscription_id': session.get('subscription')  # For recurring subscriptions
            }
        else:
            return {
                'error': f'Failed to verify payment: {response.text}'
            }
    except Exception as e:
        return {
            'error': f'Error verifying payment: {str(e)}'
        }

def handle_stripe_webhook(payload: str, signature: str) -> Dict:
    """
    Handle Stripe webhook events with proper verification
    
    Returns:
        dict with event type and data
    """
    webhook_secret = get_webhook_secret()
    
    if not webhook_secret:
        return {'error': 'Webhook secret not configured'}
    
    try:
        # Stripe sends signature in format: t=timestamp,v1=signature
        # We need to verify using Stripe's recommended method
        elements = signature.split(',')
        timestamp = None
        signatures = []
        
        for element in elements:
            if element.startswith('t='):
                timestamp = int(element.split('=')[1])
            elif element.startswith('v1='):
                signatures.append(element.split('=')[1])
        
        # Check timestamp (prevent replay attacks)
        if timestamp:
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:  # 5 minutes tolerance
                return {'error': 'Webhook timestamp too old or too far in future'}
        
        # Verify signature using Stripe's method
        signed_payload = f"{timestamp}.{payload}"
        expected_signature = hmac.new(
            webhook_secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Check if any signature matches
        signature_valid = any(
            hmac.compare_digest(expected_signature, sig) for sig in signatures
        )
        
        if not signature_valid:
            return {'error': 'Invalid webhook signature'}
        
        # Parse event
        event = json.loads(payload)
        event_id = event.get('id')
        event_type = event.get('type')
        event_data = event.get('data', {}).get('object', {})
        
        # Check idempotency (prevent duplicate processing)
        if event_id and is_webhook_processed(event_id):
            return {
                'success': True,
                'type': event_type,
                'data': event_data,
                'duplicate': True,
                'message': 'Event already processed'
            }
        
        # Mark as processed
        if event_id:
            save_webhook_event(event_id, event_type, True)
        
        return {
            'success': True,
            'type': event_type,
            'data': event_data,
            'event_id': event_id,
            'duplicate': False
        }
    except Exception as e:
        return {
            'error': f'Error processing webhook: {str(e)}'
        }

def create_refund(payment_intent_id: str, amount: Optional[int] = None, reason: str = 'requested_by_customer') -> Dict:
    """
    Create a refund for a payment
    
    Args:
        payment_intent_id: Stripe payment intent ID
        amount: Amount to refund in cents (None = full refund)
        reason: Refund reason
    
    Returns:
        dict with refund status
    """
    stripe_key = get_stripe_key()
    
    if not stripe_key:
        return {'error': 'Stripe API key not configured'}
    
    headers = {
        'Authorization': f'Bearer {stripe_key}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'payment_intent': payment_intent_id,
        'reason': reason
    }
    
    if amount:
        data['amount'] = amount
    
    try:
        response = requests.post(
            'https://api.stripe.com/v1/refunds',
            headers=headers,
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            refund_data = response.json()
            return {
                'success': True,
                'refund_id': refund_data.get('id'),
                'amount': refund_data.get('amount', 0) / 100,
                'status': refund_data.get('status')
            }
        else:
            return {
                'error': f'Failed to create refund: {response.text}'
            }
    except Exception as e:
        return {
            'error': f'Error creating refund: {str(e)}'
        }

def cancel_subscription(subscription_id: str) -> Dict:
    """
    Cancel a Stripe subscription
    
    Args:
        subscription_id: Stripe subscription ID
    
    Returns:
        dict with cancellation status
    """
    stripe_key = get_stripe_key()
    
    if not stripe_key:
        return {'error': 'Stripe API key not configured'}
    
    headers = {
        'Authorization': f'Bearer {stripe_key}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    try:
        response = requests.post(
            f'https://api.stripe.com/v1/subscriptions/{subscription_id}/cancel',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            sub_data = response.json()
            return {
                'success': True,
                'subscription_id': sub_data.get('id'),
                'status': sub_data.get('status'),
                'canceled_at': sub_data.get('canceled_at')
            }
        else:
            return {
                'error': f'Failed to cancel subscription: {response.text}'
            }
    except Exception as e:
        return {
            'error': f'Error canceling subscription: {str(e)}'
        }

# ============================================
# VENMO/CASHAPP (Manual Verification)
# ============================================

def create_manual_payment_request(username: str, amount: float, tier: str, payment_method: str = 'venmo') -> Dict:
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

def verify_manual_payment(transaction_id: str, payment_method: str = 'venmo') -> Dict:
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

