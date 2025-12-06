#!/usr/bin/env python3
"""
MySQL Database Helper for PhazeVPN Web Portal
Provides functions to replace JSON file operations with MySQL
"""

import mysql.connector
from mysql.connector import Error, pooling
from contextlib import contextmanager
import os
from typing import Optional, Dict, List, Any

# Database configuration - load from db_config.json if available
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'database': os.environ.get('MYSQL_DATABASE', 'phazevpn'),
    'user': os.environ.get('MYSQL_USER', 'phazevpn'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': False
}

# Try to load from db_config.json
try:
    import json
    from pathlib import Path
    config_file = Path(__file__).parent / 'db_config.json'
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            # Handle both nested and flat config structures
            if isinstance(file_config, dict):
                if 'database' in file_config and isinstance(file_config['database'], dict):
                    # Nested structure: {"database": {"host": "...", ...}}
                    db_info = file_config['database']
                    DB_CONFIG.update({
                        'host': db_info.get('host', DB_CONFIG['host']),
                        'database': db_info.get('database', DB_CONFIG['database']),
                        'user': db_info.get('user', DB_CONFIG['user']),
                        'password': db_info.get('password', DB_CONFIG['password']),
                    })
                else:
                    # Flat structure: {"host": "...", "database": "...", ...}
                    DB_CONFIG.update({
                        'host': file_config.get('host', DB_CONFIG['host']),
                        'database': file_config.get('database', DB_CONFIG['database']),
                        'user': file_config.get('user', DB_CONFIG['user']),
                        'password': file_config.get('password', DB_CONFIG['password']),
                    })
                    # Also check for port if present
                    if 'port' in file_config:
                        DB_CONFIG['port'] = int(file_config['port'])
except Exception as e:
    print(f"⚠️  Warning: Could not load db_config.json: {e}")
    pass  # Use defaults

# Connection pool (reuse connections)
_pool = None

def get_pool():
    """Get or create connection pool"""
    global _pool
    if _pool is None:
        pool_config = DB_CONFIG.copy()
        pool_config.update({
            'pool_name': 'phazevpn_pool',
            'pool_size': 5,
            'pool_reset_session': True
        })
        _pool = pooling.MySQLConnectionPool(**pool_config)
    return _pool

@contextmanager
def get_connection():
    """Get database connection from pool"""
    pool = get_pool()
    connection = pool.get_connection()
    try:
        yield connection
        connection.commit()
    except Error:
        connection.rollback()
        raise
    finally:
        connection.close()

# ============================================
# USER OPERATIONS
# ============================================

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user by username from database.
    
    Args:
        username: Username to look up
        
    Returns:
        User dictionary with all fields, or None if not found
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()

def create_user(username: str, email: str, password_hash: str, role: str = 'user') -> bool:
    """
    Create a new user in the database.
    
    Args:
        username: Unique username (3-30 chars, alphanumeric + underscore/hyphen)
        email: User email address
        password_hash: Bcrypt hashed password
        role: User role ('admin', 'moderator', or 'user')
        
    Returns:
        True if user created successfully, False if username already exists
        
    Raises:
        Error: Database error (other than duplicate entry)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
            """, (username, email, password_hash, role))
            return True
    except Error as e:
        if e.errno == 1062:  # Duplicate entry
            return False
        raise

def update_user(username: str, **kwargs) -> bool:
    """
    Update user fields in database.
    
    Args:
        username: Username of user to update
        **kwargs: Fields to update (email, password_hash, role)
        
    Returns:
        True if user was updated, False if no valid fields provided
        
    Note:
        Only 'email', 'password_hash', and 'role' fields are allowed
    """
    allowed_fields = ['email', 'password_hash', 'role']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values()) + [username]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {set_clause} WHERE username = %s", values)
        return cursor.rowcount > 0

def list_users() -> List[Dict[str, Any]]:
    """List all users"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, role, created_at FROM users ORDER BY username")
        return cursor.fetchall()

# ============================================
# CLIENT OPERATIONS
# ============================================

def get_user_clients(username: str) -> List[Dict[str, Any]]:
    """Get all clients for a user"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT client_name, protocol, created_at
            FROM clients
            WHERE username = %s
            ORDER BY created_at DESC
        """, (username,))
        return cursor.fetchall()

def create_client(username: str, client_name: str, protocol: str = 'openvpn') -> bool:
    """Create new client"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (username, client_name, protocol)
                VALUES (%s, %s, %s)
            """, (username, client_name, protocol))
            return True
    except Error as e:
        if e.errno == 1062:  # Duplicate entry
            return False
        raise

def delete_client(username: str, client_name: str, protocol: str = None) -> bool:
    """Delete client"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if protocol:
            cursor.execute("""
                DELETE FROM clients
                WHERE username = %s AND client_name = %s AND protocol = %s
            """, (username, client_name, protocol))
        else:
            cursor.execute("""
                DELETE FROM clients
                WHERE username = %s AND client_name = %s
            """, (username, client_name))
        return cursor.rowcount > 0

# ============================================
# PAYMENT OPERATIONS
# ============================================

def create_payment(username: str, amount: float, currency: str = 'usd', 
                  payment_method: str = None, transaction_id: str = None) -> int:
    """Create payment record"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO payments (username, amount, currency, payment_method, transaction_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, amount, currency, payment_method, transaction_id))
        return cursor.lastrowid

def update_payment_status(payment_id: int, status: str, transaction_id: str = None) -> bool:
    """Update payment status"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if transaction_id:
            cursor.execute("""
                UPDATE payments
                SET status = %s, transaction_id = %s
                WHERE id = %s
            """, (status, transaction_id, payment_id))
        else:
            cursor.execute("""
                UPDATE payments
                SET status = %s
                WHERE id = %s
            """, (status, payment_id))
        return cursor.rowcount > 0

def get_user_payments(username: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get user payment history"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, amount, currency, status, payment_method, transaction_id, created_at
            FROM payments
            WHERE username = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (username, limit))
        return cursor.fetchall()

# ============================================
# CONNECTION HISTORY
# ============================================

def log_connection(username: str, client_name: str, protocol: str, 
                  action: str = 'connect', ip_address: str = None) -> bool:
    """NO LOGGING - Complete privacy - we don't track connections"""
    # DO NOTHING - Complete anonymity
    # We don't store connection history or IP addresses
    return True

def get_connection_history(username: str = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """NO HISTORY - Complete privacy"""
    # We don't track connection history - complete anonymity
    return []

# ============================================
# RATE LIMITING (MySQL alternative to Redis)
# ============================================

def check_rate_limit(username: str, endpoint: str = 'default', 
                    max_attempts: int = 5, window_seconds: int = 900) -> tuple[bool, int]:
    """
    Check rate limit by username (NO IP tracking for privacy).
    
    Args:
        username: Username to check rate limit for
        endpoint: Endpoint identifier (default: 'default')
        max_attempts: Maximum attempts allowed in time window (default: 5)
        window_seconds: Time window in seconds (default: 900 = 15 minutes)
        
    Returns:
        Tuple of (is_allowed, current_attempts)
        - is_allowed: True if under limit, False if rate limited
        - current_attempts: Current number of attempts in window
        
    Privacy:
        Rate limiting uses username only, NOT IP address.
        This prevents abuse without tracking user IPs.
    """
    # Rate limit by username, NOT IP address
    # This prevents abuse without tracking IPs - complete privacy
    if not username:
        return (True, max_attempts)  # No username = no rate limit
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Clean old entries
        cursor.execute("""
            DELETE FROM rate_limits
            WHERE window_start < DATE_SUB(NOW(), INTERVAL %s SECOND)
        """, (window_seconds,))
        
        # Check current attempts (by username, NOT IP)
        cursor.execute("""
            SELECT attempts
            FROM rate_limits
            WHERE username = %s AND endpoint = %s
            AND window_start > DATE_SUB(NOW(), INTERVAL %s SECOND)
        """, (username, endpoint, window_seconds))
        
        result = cursor.fetchone()
        if result:
            attempts = result[0]
            if attempts >= max_attempts:
                return False, attempts
            
            # Increment attempts
            cursor.execute("""
                UPDATE rate_limits
                SET attempts = attempts + 1
                WHERE username = %s AND endpoint = %s
            """, (username, endpoint))
            return True, attempts + 1
        else:
            # Create new entry (username only, NO IP)
            cursor.execute("""
                INSERT INTO rate_limits (username, endpoint, attempts)
                VALUES (%s, %s, 1)
            """, (username, endpoint))
            return True, 1

def reset_rate_limit(username: str, endpoint: str = 'default') -> bool:
    """Reset rate limit by username - NO IP tracking"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM rate_limits
            WHERE username = %s AND endpoint = %s
        """, (username, endpoint))
        return cursor.rowcount > 0

# ============================================
# INITIALIZATION
# ============================================

def init_database():
    """Initialize database connection"""
    try:
        pool = get_pool()
        conn = pool.get_connection()
        conn.close()
        return True
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == '__main__':
    # Test connection
    if init_database():
        print("✅ MySQL connection successful")
    else:
        print("❌ MySQL connection failed")

