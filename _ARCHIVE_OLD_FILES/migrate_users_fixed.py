#!/usr/bin/env python3
import json
import sys
import os

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Installing mysql-connector-python...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'mysql-connector-python'], check=True)
    import mysql.connector
    from mysql.connector import Error

# Database config
db_config = {
    'host': 'localhost',
    'database': 'phazevpn',
    'user': 'phazevpn',
    'password': 'PhazeVPN2025SecureDB!'
}

# Connect to MySQL
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Load users from JSON
    users_file = '/opt/phaze-vpn/users.json'
    if not os.path.exists(users_file):
        users_file = '/opt/phaze-vpn/web-portal/users.json'
    
    if os.path.exists(users_file):
        print(f"Loading users from {users_file}...")
        with open(users_file) as f:
            users_data = json.load(f)
        
        users = users_data.get('users', {})
        print(f"Found {len(users)} users to migrate")
        
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
                print(f"  ✅ Migrated: {username}")
            except Exception as e:
                print(f"  ❌ Error migrating {username}: {e}")
                skipped += 1
        
        conn.commit()
        print(f"\n✅ Successfully migrated {migrated} users to MySQL")
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} users due to errors")
    else:
        print(f"⚠️  users.json not found at {users_file}, skipping migration")
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f"❌ MySQL Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

