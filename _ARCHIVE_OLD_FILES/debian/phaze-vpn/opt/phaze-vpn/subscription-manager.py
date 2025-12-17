#!/usr/bin/env python3
"""
PhazeVPN Subscription Management System
Handles free and paid subscriptions, payments, and user upgrades
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import uuid

VPN_DIR = Path(__file__).parent
SUBSCRIPTIONS_FILE = VPN_DIR / 'subscriptions.json'
USERS_FILE = VPN_DIR / 'users.json'

# Subscription tiers
TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'price_display': 'Free',
        'features': [
            'Unlimited bandwidth',
            'Unlimited connections',
            'All server locations',
            'Standard support'
        ]
    },
    'premium': {
        'name': 'Premium',
        'price': 9.99,
        'price_display': '$9.99/month',
        'billing_cycle': 'monthly',
        'features': [
            'Unlimited bandwidth',
            'Unlimited connections',
            'All server locations',
            'Priority support',
            'Advanced features',
            'Early access to new features'
        ]
    },
    'pro': {
        'name': 'Pro',
        'price': 19.99,
        'price_display': '$19.99/month',
        'billing_cycle': 'monthly',
        'features': [
            'Unlimited bandwidth',
            'Unlimited connections',
            'All server locations',
            'Priority support',
            'Advanced features',
            'Early access to new features',
            'Dedicated support channel'
        ]
    }
}

def load_subscriptions():
    """Load subscriptions from file"""
    if SUBSCRIPTIONS_FILE.exists():
        try:
            with open(SUBSCRIPTIONS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        'subscriptions': {},
        'payments': {},
        'settings': {
            'stripe_public_key': '',
            'stripe_secret_key': '',
            'stripe_webhook_secret': ''
        }
    }

def save_subscriptions(data):
    """Save subscriptions to file"""
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_user_subscription(username):
    """Get subscription info for a user"""
    data = load_subscriptions()
    sub = data['subscriptions'].get(username, {})
    
    # Default to free if no subscription
    if not sub:
        return {
            'tier': 'free',
            'status': 'active',
            'started': datetime.now().isoformat(),
            'expires': None,
            'payment_method': None
        }
    
    return sub

def set_user_subscription(username, tier, payment_id=None):
    """Set or update user subscription"""
    data = load_subscriptions()
    
    if username not in data['subscriptions']:
        data['subscriptions'][username] = {}
    
    sub = data['subscriptions'][username]
    sub['tier'] = tier
    sub['status'] = 'active'
    sub['updated'] = datetime.now().isoformat()
    
    if not sub.get('started'):
        sub['started'] = datetime.now().isoformat()
    
    # Set expiration for paid tiers
    if tier != 'free':
        if tier == 'premium':
            sub['expires'] = (datetime.now() + timedelta(days=30)).isoformat()
        elif tier == 'pro':
            sub['expires'] = (datetime.now() + timedelta(days=30)).isoformat()
        sub['payment_method'] = 'stripe'
        if payment_id:
            sub['payment_id'] = payment_id
    else:
        sub['expires'] = None
        sub['payment_method'] = None
    
    save_subscriptions(data)
    return sub

def cancel_subscription(username):
    """Cancel user subscription (downgrade to free)"""
    return set_user_subscription(username, 'free')

def check_subscription_status(username):
    """Check if subscription is active"""
    sub = get_user_subscription(username)
    
    if sub['tier'] == 'free':
        return True  # Free is always active
    
    if sub['status'] != 'active':
        return False
    
    # Check expiration
    if sub.get('expires'):
        expires = datetime.fromisoformat(sub['expires'])
        if datetime.now() > expires:
            # Auto-downgrade to free
            set_user_subscription(username, 'free')
            return False
    
    return True

def get_tier_info(tier):
    """Get information about a subscription tier"""
    return TIERS.get(tier, TIERS['free'])

def create_payment_intent(username, tier, amount):
    """Create a payment intent (for Stripe integration)"""
    data = load_subscriptions()
    
    payment_id = str(uuid.uuid4())
    
    if 'payments' not in data:
        data['payments'] = {}
    
    data['payments'][payment_id] = {
        'username': username,
        'tier': tier,
        'amount': amount,
        'status': 'pending',
        'created': datetime.now().isoformat()
    }
    
    save_subscriptions(data)
    return payment_id

def record_payment(payment_id, status='completed'):
    """Record payment completion"""
    data = load_subscriptions()
    
    if payment_id in data['payments']:
        payment = data['payments'][payment_id]
        payment['status'] = status
        payment['completed'] = datetime.now().isoformat()
        
        if status == 'completed':
            # Upgrade user
            set_user_subscription(payment['username'], payment['tier'], payment_id)
        
        save_subscriptions(data)
        return True
    
    return False

def get_all_subscriptions():
    """Get all subscriptions (admin function)"""
    data = load_subscriptions()
    return data['subscriptions']

def get_revenue_stats():
    """Get revenue statistics (admin function)"""
    data = load_subscriptions()
    
    total_revenue = 0
    active_paid = 0
    free_users = 0
    
    for username, sub in data['subscriptions'].items():
        if sub['tier'] == 'free':
            free_users += 1
        else:
            if check_subscription_status(username):
                active_paid += 1
                tier_info = get_tier_info(sub['tier'])
                total_revenue += tier_info['price']
    
    return {
        'total_revenue': total_revenue,
        'monthly_recurring_revenue': total_revenue,
        'active_paid_subscriptions': active_paid,
        'free_users': free_users,
        'total_users': len(data['subscriptions'])
    }

