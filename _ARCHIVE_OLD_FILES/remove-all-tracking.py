#!/usr/bin/env python3
"""
REMOVE ALL TRACKING - Complete Privacy Fix
Removes ALL logging, tracking, IP storage, and data collection
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / 'web-portal'
APP_PY = WEB_PORTAL_DIR / 'app.py'
MYSQL_DB_PY = WEB_PORTAL_DIR / 'mysql_db.py'

print("=" * 80)
print("🔒 REMOVING ALL TRACKING - COMPLETE PRIVACY FIX")
print("=" * 80)
print()

# Fix 1: Remove activity logging function
print("[1/7] Removing activity logging...")
if APP_PY.exists():
    content = APP_PY.read_text()
    
    # Replace log_activity to do nothing
    old_log = r'def log_activity\(user, action, details=""\):.*?f\.write\(entry\)'
    new_log = '''def log_activity(user, action, details=""):
    """NO LOGGING - Complete privacy - we don't track user activity"""
    # DO NOTHING - Complete anonymity
    pass'''
    
    content = re.sub(old_log, new_log, content, flags=re.DOTALL)
    
    # Replace get_activity_logs to return empty
    old_get_logs = r'def get_activity_logs\(limit=\d+\):.*?return \[\]'
    new_get_logs = '''def get_activity_logs(limit=100):
    """NO LOGS - Complete privacy"""
    return []  # We don't track user activity'''
    
    content = re.sub(old_get_logs, new_get_logs, content, flags=re.DOTALL)
    
    APP_PY.write_text(content)
    print("   ✅ Activity logging removed")

# Fix 2: Remove connection history
print("[2/7] Removing connection history...")
if APP_PY.exists():
    content = APP_PY.read_text()
    
    # Replace update_connection_history to do nothing
    old_history = r'def update_connection_history\(connections\):.*?safe_json_write\(CONNECTION_HISTORY, history'
    new_history = '''def update_connection_history(connections):
    """NO HISTORY - Complete privacy - we don't track connections"""
    # DO NOTHING - Complete anonymity
    pass'''
    
    content = re.sub(old_history, new_history, content, flags=re.DOTALL)
    
    APP_PY.write_text(content)
    print("   ✅ Connection history removed")

# Fix 3: Remove IP address storage from mysql_db.py
print("[3/7] Removing IP address storage...")
if MYSQL_DB_PY.exists():
    content = MYSQL_DB_PY.read_text()
    
    # Replace log_connection to NOT store IP
    old_log_conn = r'def log_connection\(username: str, client_name: str, protocol: str,.*?ip_address: str = None\).*?return True'
    new_log_conn = '''def log_connection(username: str, client_name: str, protocol: str, 
                  action: str = 'connect', ip_address: str = None) -> bool:
    """NO LOGGING - Complete privacy - we don't track connections"""
    # DO NOTHING - Complete anonymity
    # We don't store IP addresses or connection history
    return True'''
    
    content = re.sub(old_log_conn, new_log_conn, content, flags=re.DOTALL)
    
    # Replace get_connection_history to return empty
    old_get_history = r'def get_connection_history\(username: str = None, limit: int = 1000\).*?return cursor\.fetchall\(\)'
    new_get_history = '''def get_connection_history(username: str = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """NO HISTORY - Complete privacy"""
    return []  # We don't track connection history'''
    
    content = re.sub(old_get_history, new_get_history, content, flags=re.DOTALL)
    
    MYSQL_DB_PY.write_text(content)
    print("   ✅ IP address storage removed")

# Fix 4: Fix rate limiting (no IP)
print("[4/7] Fixing rate limiting (username only, no IP)...")
if MYSQL_DB_PY.exists():
    content = MYSQL_DB_PY.read_text()
    
    # Replace check_rate_limit to use username instead of IP
    old_rate_limit = r'def check_rate_limit\(ip_address: str, endpoint: str = \'default\',.*?return \(not exceeded, remaining\)'
    new_rate_limit = '''def check_rate_limit(username: str, endpoint: str = 'default', 
                    max_attempts: int = 5, window_seconds: int = 900) -> tuple[bool, int]:
    """Check rate limit by username ONLY - NO IP tracking for privacy"""
    # Rate limit by username, NOT IP address
    # This prevents abuse without tracking IPs
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Clean old entries
        cursor.execute("""
            DELETE FROM rate_limits
            WHERE window_start < DATE_SUB(NOW(), INTERVAL %s SECOND)
        """, (window_seconds,))
        
        # Check current attempts (by username, not IP)
        cursor.execute("""
            SELECT attempts FROM rate_limits
            WHERE username = %s AND endpoint = %s
            AND window_start >= DATE_SUB(NOW(), INTERVAL %s SECOND)
            LIMIT 1
        """, (username, endpoint, window_seconds))
        
        result = cursor.fetchone()
        if result:
            attempts = result[0]
            if attempts >= max_attempts:
                return (False, 0)  # Rate limit exceeded
            # Increment
            cursor.execute("""
                UPDATE rate_limits SET attempts = attempts + 1
                WHERE username = %s AND endpoint = %s
            """, (username, endpoint))
            remaining = max_attempts - attempts - 1
        else:
            # Create new entry (username only, NO IP)
            cursor.execute("""
                INSERT INTO rate_limits (username, endpoint, attempts)
                VALUES (%s, %s, 1)
            """, (username, endpoint))
            remaining = max_attempts - 1
        
        conn.commit()
        return (True, remaining)'''
    
    content = re.sub(old_rate_limit, new_rate_limit, content, flags=re.DOTALL)
    
    # Replace reset_rate_limit
    old_reset = r'def reset_rate_limit\(ip_address: str, endpoint: str = \'default\'\).*?return True'
    new_reset = '''def reset_rate_limit(username: str, endpoint: str = 'default') -> bool:
    """Reset rate limit by username - NO IP tracking"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM rate_limits
            WHERE username = %s AND endpoint = %s
        """, (username, endpoint))
        conn.commit()
        return True'''
    
    content = re.sub(old_reset, new_reset, content, flags=re.DOTALL)
    
    MYSQL_DB_PY.write_text(content)
    print("   ✅ Rate limiting fixed (username only)")

# Fix 5: Remove real_ip from API responses
print("[5/7] Removing real_ip from API responses...")
if APP_PY.exists():
    content = APP_PY.read_text()
    
    # Remove real_ip from all JSON responses
    content = re.sub(r"'real_ip':[^,}]+", "", content)
    content = re.sub(r'"real_ip":[^,}]+", "", content)
    content = re.sub(r'real_ip.*?N/A', "", content)
    
    APP_PY.write_text(content)
    print("   ✅ real_ip removed from responses")

# Fix 6: Remove request.remote_addr usage
print("[6/7] Removing IP address capture...")
if APP_PY.exists():
    content = APP_PY.read_text()
    
    # Replace check_rate_limit(request.remote_addr) with check_rate_limit(username)
    content = re.sub(
        r'check_rate_limit\(request\.remote_addr\)',
        "check_rate_limit(session.get('username', 'anonymous'))",
        content
    )
    
    # Remove any IP address variables
    content = re.sub(r'ip_address\s*=\s*request\.remote_addr', '# Privacy: No IP capture', content)
    content = re.sub(r'ip\s*=\s*request\.remote_addr', '# Privacy: No IP capture', content)
    
    APP_PY.write_text(content)
    print("   ✅ IP address capture removed")

# Fix 7: Create database migration to remove IP columns
print("[7/7] Creating database migration to remove IP columns...")
migration_file = WEB_PORTAL_DIR / 'remove_ip_tracking_migration.sql'
migration_content = """-- Remove IP tracking for complete privacy
-- Run this on your database to remove all IP address storage

-- Remove IP column from connection_history
ALTER TABLE connection_history DROP COLUMN IF EXISTS ip_address;

-- Remove IP column from rate_limits (if exists)
ALTER TABLE rate_limits DROP COLUMN IF EXISTS ip_address;

-- Change rate_limits to use username instead of IP
ALTER TABLE rate_limits ADD COLUMN IF NOT EXISTS username VARCHAR(255);
ALTER TABLE rate_limits DROP PRIMARY KEY IF EXISTS;
ALTER TABLE rate_limits ADD PRIMARY KEY (username, endpoint, window_start);

-- Delete all existing connection history (contains IPs)
TRUNCATE TABLE connection_history;

-- Delete all existing rate limits (contains IPs)
TRUNCATE TABLE rate_limits;

-- Optional: Drop connection_history table entirely for complete privacy
-- DROP TABLE IF EXISTS connection_history;
"""
migration_file.write_text(migration_content)
print("   ✅ Database migration created: remove_ip_tracking_migration.sql")

print()
print("=" * 80)
print("✅ PRIVACY FIXES COMPLETE!")
print("=" * 80)
print()
print("📋 Next Steps:")
print("1. Review the changes")
print("2. Run database migration:")
print("   mysql -u user -p database < web-portal/remove_ip_tracking_migration.sql")
print("3. Test the application")
print("4. Verify no IP addresses are stored")
print("5. Verify no connection history is stored")
print()
print("🔒 Privacy Status: COMPLETE ANONYMITY")
print("   - No IP tracking")
print("   - No connection history")
print("   - No activity logging")
print("   - Complete ghost mode")
