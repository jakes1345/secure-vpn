#!/usr/bin/env python3
"""
Email Rate Limiting - Prevent email spam/abuse
Rate limits per recipient, per sender, and globally
"""

import time
from typing import Tuple, Optional
import os

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Rate limit configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# Rate limits (per hour)
RATE_LIMITS = {
    'per_recipient': 10,  # Max 10 emails per recipient per hour
    'per_sender': 100,     # Max 100 emails per sender per hour
    'global': 1000,        # Max 1000 emails globally per hour
}

def get_redis_connection():
    """Get Redis connection"""
    if not REDIS_AVAILABLE:
        return None
    
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5
        )
        r.ping()
        return r
    except:
        return None

def check_rate_limit(recipient: str, sender: str = 'system') -> Tuple[bool, Optional[str]]:
    """
    Check if email sending is rate limited
    
    Args:
        recipient: Recipient email address
        sender: Sender identifier (email or 'system')
    
    Returns:
        (is_allowed, error_message)
    """
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        # If Redis unavailable, allow (fallback)
        return True, None
    
    now = time.time()
    hour_key = int(now / 3600)  # Hour bucket
    
    # Check per-recipient limit
    recipient_key = f"email:rate:recipient:{recipient}:{hour_key}"
    recipient_count = redis_conn.get(recipient_key)
    if recipient_count and int(recipient_count) >= RATE_LIMITS['per_recipient']:
        return False, f"Rate limit exceeded for recipient (max {RATE_LIMITS['per_recipient']} per hour)"
    
    # Check per-sender limit
    sender_key = f"email:rate:sender:{sender}:{hour_key}"
    sender_count = redis_conn.get(sender_key)
    if sender_count and int(sender_count) >= RATE_LIMITS['per_sender']:
        return False, f"Rate limit exceeded for sender (max {RATE_LIMITS['per_sender']} per hour)"
    
    # Check global limit
    global_key = f"email:rate:global:{hour_key}"
    global_count = redis_conn.get(global_key)
    if global_count and int(global_count) >= RATE_LIMITS['global']:
        return False, f"Global rate limit exceeded (max {RATE_LIMITS['global']} per hour)"
    
    return True, None

def increment_rate_limit(recipient: str, sender: str = 'system'):
    """Increment rate limit counters"""
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        return
    
    now = time.time()
    hour_key = int(now / 3600)
    expire_time = 3600  # 1 hour
    
    # Increment counters
    recipient_key = f"email:rate:recipient:{recipient}:{hour_key}"
    sender_key = f"email:rate:sender:{sender}:{hour_key}"
    global_key = f"email:rate:global:{hour_key}"
    
    redis_conn.incr(recipient_key)
    redis_conn.expire(recipient_key, expire_time)
    
    redis_conn.incr(sender_key)
    redis_conn.expire(sender_key, expire_time)
    
    redis_conn.incr(global_key)
    redis_conn.expire(global_key, expire_time)
