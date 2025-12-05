#!/usr/bin/env python3
"""
Rate Limiting Module with File-Based Persistence
Provides persistent rate limiting that survives server restarts
"""

import json
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

# Rate limit configuration
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
RATE_LIMIT_FILE = Path(__file__).parent / 'data' / 'rate_limits.json'

# Ensure data directory exists
RATE_LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_rate_limits():
    """Load rate limit data from file"""
    if not RATE_LIMIT_FILE.exists():
        return {}
    
    try:
        with open(RATE_LIMIT_FILE, 'r') as f:
            data = json.load(f)
            # Convert timestamp strings back to floats
            result = {}
            for ip, timestamps in data.items():
                result[ip] = [float(ts) for ts in timestamps]
            return result
    except (json.JSONDecodeError, IOError, ValueError):
        return {}


def save_rate_limits(rate_limits):
    """Save rate limit data to file"""
    try:
        # Convert floats to strings for JSON serialization
        data = {ip: [str(ts) for ts in timestamps] for ip, timestamps in rate_limits.items()}
        
        # Use file locking if available
        try:
            from file_locking import safe_json_write
            safe_json_write(RATE_LIMIT_FILE, data, create_backup=False)
        except ImportError:
            # Fallback to regular write
            with open(RATE_LIMIT_FILE, 'w') as f:
                json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Warning: Failed to save rate limits: {e}")


def cleanup_old_attempts(rate_limits, now=None):
    """Remove attempts older than RATE_LIMIT_WINDOW"""
    if now is None:
        now = time.time()
    
    cleaned = {}
    for ip, timestamps in rate_limits.items():
        recent = [ts for ts in timestamps if now - ts < RATE_LIMIT_WINDOW]
        if recent:
            cleaned[ip] = recent
    
    return cleaned


def check_rate_limit(ip, max_attempts=None, window=None):
    """
    Check if IP is rate limited
    
    Args:
        ip: IP address to check
        max_attempts: Maximum attempts allowed (defaults to RATE_LIMIT_MAX)
        window: Time window in seconds (defaults to RATE_LIMIT_WINDOW)
    
    Returns:
        True if allowed, False if rate limited
    """
    if max_attempts is None:
        max_attempts = RATE_LIMIT_MAX
    if window is None:
        window = RATE_LIMIT_WINDOW
    
    now = time.time()
    
    # Load current rate limits
    rate_limits = load_rate_limits()
    
    # Clean up old attempts
    rate_limits = cleanup_old_attempts(rate_limits, now)
    
    # Check if IP is rate limited
    if ip not in rate_limits:
        rate_limits[ip] = []
    
    attempts = rate_limits[ip]
    
    # Remove attempts outside the window
    attempts = [ts for ts in attempts if now - ts < window]
    
    if len(attempts) >= max_attempts:
        # Rate limited - save current state
        rate_limits[ip] = attempts
        save_rate_limits(rate_limits)
        return False
    
    # Add new attempt
    attempts.append(now)
    rate_limits[ip] = attempts
    
    # Save updated rate limits
    save_rate_limits(rate_limits)
    
    return True


def reset_rate_limit(ip):
    """Reset rate limit for an IP address"""
    rate_limits = load_rate_limits()
    if ip in rate_limits:
        del rate_limits[ip]
        save_rate_limits(rate_limits)


def get_rate_limit_status(ip):
    """Get current rate limit status for an IP"""
    now = time.time()
    rate_limits = load_rate_limits()
    
    if ip not in rate_limits:
        return {
            'limited': False,
            'attempts': 0,
            'remaining': RATE_LIMIT_MAX,
            'reset_in': 0
        }
    
    attempts = [ts for ts in rate_limits[ip] if now - ts < RATE_LIMIT_WINDOW]
    
    if len(attempts) >= RATE_LIMIT_MAX:
        # Calculate when the oldest attempt expires
        oldest = min(attempts)
        reset_in = int((oldest + RATE_LIMIT_WINDOW) - now)
        return {
            'limited': True,
            'attempts': len(attempts),
            'remaining': 0,
            'reset_in': max(0, reset_in)
        }
    
    return {
        'limited': False,
        'attempts': len(attempts),
        'remaining': RATE_LIMIT_MAX - len(attempts),
        'reset_in': 0
    }

