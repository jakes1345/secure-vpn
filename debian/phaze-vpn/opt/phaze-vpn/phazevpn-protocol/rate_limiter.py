#!/usr/bin/env python3
"""
PhazeVPN Protocol - Rate Limiting
Prevent abuse with per-user rate limits
"""

import time
from collections import defaultdict
from typing import Dict

class TokenBucket:
    """
    Token bucket algorithm for rate limiting
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens (bytes)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int) -> bool:
        """
        Try to consume tokens
        Returns True if successful, False if rate limit exceeded
        """
        # Refill tokens based on time elapsed
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        else:
            return False
    
    def get_available(self) -> int:
        """Get available tokens"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        return int(self.tokens)

class RateLimiter:
    """
    Per-user rate limiting
    """
    
    def __init__(self, default_limit_bytes_per_sec: int = 10000000, burst_size: int = 50000000):
        """
        Args:
            default_limit_bytes_per_sec: Default rate limit (10MB/s)
            burst_size: Burst capacity (50MB)
        """
        self.default_limit = default_limit_bytes_per_sec
        self.burst_size = burst_size
        self.limits: Dict[str, TokenBucket] = {}
        self.custom_limits: Dict[str, int] = {}  # session_id -> custom limit
    
    def set_limit(self, session_id: str, bytes_per_sec: int):
        """Set custom rate limit for session"""
        self.custom_limits[session_id] = bytes_per_sec
        if session_id in self.limits:
            # Recreate with new limit
            limit = bytes_per_sec
            self.limits[session_id] = TokenBucket(self.burst_size, limit)
    
    def get_limit(self, session_id: str) -> int:
        """Get rate limit for session"""
        return self.custom_limits.get(session_id, self.default_limit)
    
    def check_rate_limit(self, session_id: str, bytes_to_send: int) -> bool:
        """
        Check if request is within rate limit
        Returns True if allowed, False if rate limited
        """
        if session_id not in self.limits:
            limit = self.get_limit(session_id)
            self.limits[session_id] = TokenBucket(self.burst_size, limit)
        
        bucket = self.limits[session_id]
        return bucket.consume(bytes_to_send)
    
    def remove_session(self, session_id: str):
        """Remove rate limiter for session"""
        if session_id in self.limits:
            del self.limits[session_id]
        if session_id in self.custom_limits:
            del self.custom_limits[session_id]
    
    def get_status(self, session_id: str) -> dict:
        """Get rate limit status for session"""
        if session_id not in self.limits:
            return {'allowed': True, 'available_bytes': self.burst_size}
        
        bucket = self.limits[session_id]
        available = bucket.get_available()
        limit = self.get_limit(session_id)
        
        return {
            'allowed': available > 0,
            'available_bytes': available,
            'limit_bytes_per_sec': limit,
            'burst_capacity': self.burst_size
        }

class ConnectionLimiter:
    """
    Limit number of concurrent connections per user
    """
    
    def __init__(self, max_connections_per_user: int = 5):
        self.max_connections = max_connections_per_user
        self.user_connections: Dict[str, set] = defaultdict(set)  # username -> set of session_ids
    
    def can_connect(self, username: str, session_id: str) -> bool:
        """Check if user can make another connection"""
        if username not in self.user_connections:
            return True
        
        connections = self.user_connections[username]
        
        # Remove stale sessions
        connections = {sid for sid in connections if self._is_session_active(sid)}
        self.user_connections[username] = connections
        
        # Check limit
        if len(connections) >= self.max_connections:
            return False
        
        # Add new connection
        connections.add(session_id)
        return True
    
    def disconnect(self, username: str, session_id: str):
        """Remove connection"""
        if username in self.user_connections:
            self.user_connections[username].discard(session_id)
    
    def _is_session_active(self, session_id: str) -> bool:
        """Check if session is still active (placeholder)"""
        # This would check with session manager
        return True

