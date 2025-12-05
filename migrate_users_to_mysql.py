#!/usr/bin/env python3
"""
Migrate users from JSON to MySQL
"""
import json
import sys
import os
sys.path.insert(0, '/opt/phaze-vpn/web-portal')

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Installing mysql-connector-python...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'mysql-connector-python'], check=True)
    import mysql.connector
    from mysql.connector import Error

# Load config
try:
    with open('/opt/phaze-vpn/web-portal/db_config.json') as f:
        config = json.load(f)
except:
    config = {
        'database': {
            'host': 'localhost',
            'database': 'phazevpn',
            'user': 'phazevpn',
            'password': 'PhazeVPN2025SecureDB!'
        }
    }

# Connect to MySQL
try:
    conn = mysql.connector.connect(
        host=config.get('database', {}).get('host', 'localhost'),
        database=config.get('database', {}).get('database', 'phazevpn'),
        user=config.get('database', {}).get('user', 'phazevpn'),
        password=config.get('database', {}).get('password', 'PhazeVPN2025SecureDB!')
    )
    
    cursor = conn.cursor()
    
    # Load users from JSON
    users_file = '/opt/phaze-vpn/users.json'
    if not os.path.exists(users_file):
        users_file = '/opt/phaze-vpn/web-portal/users.json'
    
    if os.path.exists(users_file):
        with open(users_file) as f:
            users_data = json.load(f)
        
        users = users_data.get('users', {})
        
        # Migrate users
        migrated = 0
        skipped = 0
        for username, user_data in users.items():
            try:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, email_verified, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        password_hash = VALUES(password_hash),
                        email = VALUES(email),
                        email_verified = VALUES(email_verified),
                        role = VALUES(role)
                """, (
                    username,
                    user_data.get('password', ''),
                    user_data.get('email', ''),
                    user_data.get('email_verified', False),
                    user_data.get('role', 'user')
                ))
                migrated += 1
            except Exception as e:
                print(f"Error migrating {username}: {e}")
                skipped += 1
        
        conn.commit()
        print(f"✅ Migrated {migrated} users to MySQL")
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} users due to errors")
    else:
        print("⚠️  users.json not found, skipping migration")
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f"❌ MySQL Error: {e}")
    sys.exit(1)

