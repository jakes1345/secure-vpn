#!/usr/bin/env python3
"""
MySQL Migration Script for PhazeVPN Web Portal
Migrates data from JSON files to MySQL database
"""

import json
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from datetime import datetime
import bcrypt
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'phazevpn',
    'user': 'phazevpn',
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Paths
VPN_DIR = Path('/opt/phaze-vpn')
USERS_FILE = VPN_DIR / 'users.json'
CLIENTS_FILE = VPN_DIR / 'data' / 'clients.json'
PAYMENT_REQUESTS_FILE = VPN_DIR / 'logs' / 'payment-requests.json'
CONNECTION_HISTORY = VPN_DIR / 'logs' / 'connection-history.json'

def create_tables(cursor):
    """Create MySQL tables"""
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255),
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'moderator', 'user') DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Clients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            client_name VARCHAR(100) NOT NULL,
            protocol ENUM('openvpn', 'wireguard', 'phazevpn') DEFAULT 'openvpn',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_client_name (client_name),
            UNIQUE KEY unique_client (username, client_name, protocol)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'usd',
            status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
            payment_method VARCHAR(50),
            transaction_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Sessions table (for Flask sessions if using MySQL backend)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100),
            data TEXT,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session_id (session_id),
            INDEX idx_expires_at (expires_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Connection history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connection_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100),
            client_name VARCHAR(100),
            protocol VARCHAR(50),
            action ENUM('connect', 'disconnect') DEFAULT 'connect',
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_client_name (client_name),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    print("✅ Tables created")

def migrate_users(cursor, users_file):
    """Migrate users from JSON to MySQL"""
    if not users_file.exists():
        print(f"⚠️  Users file not found: {users_file}")
        return
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    migrated = 0
    for username, user_data in users.items():
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    email = VALUES(email),
                    password_hash = VALUES(password_hash),
                    role = VALUES(role)
            """, (
                username,
                user_data.get('email'),
                user_data.get('password'),
                user_data.get('role', 'user'),
                user_data.get('created', datetime.now().isoformat())
            ))
            migrated += 1
        except Error as e:
            print(f"❌ Error migrating user {username}: {e}")
    
    print(f"✅ Migrated {migrated} users")

def migrate_clients(cursor, clients_file):
    """Migrate clients from JSON to MySQL"""
    if not clients_file.exists():
        print(f"⚠️  Clients file not found: {clients_file}")
        return
    
    with open(clients_file, 'r') as f:
        clients_data = json.load(f)
    
    migrated = 0
    for username, clients in clients_data.items():
        if not isinstance(clients, list):
            continue
        
        for client in clients:
            try:
                client_name = client.get('name') or client.get('client_name')
                protocol = client.get('protocol', 'openvpn')
                
                cursor.execute("""
                    INSERT INTO clients (username, client_name, protocol, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    username,
                    client_name,
                    protocol,
                    client.get('created', datetime.now().isoformat())
                ))
                migrated += 1
            except Error as e:
                print(f"❌ Error migrating client {client_name}: {e}")
    
    print(f"✅ Migrated {migrated} clients")

def migrate_payments(cursor, payments_file):
    """Migrate payments from JSON to MySQL"""
    if not payments_file.exists():
        print(f"⚠️  Payments file not found: {payments_file}")
        return
    
    with open(payments_file, 'r') as f:
        payments = json.load(f)
    
    migrated = 0
    for payment_id, payment_data in payments.items():
        try:
            cursor.execute("""
                INSERT INTO payments (username, amount, currency, status, payment_method, transaction_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                payment_data.get('username'),
                payment_data.get('amount', 0),
                payment_data.get('currency', 'usd'),
                payment_data.get('status', 'pending'),
                payment_data.get('payment_method'),
                payment_data.get('transaction_id'),
                payment_data.get('created_at', datetime.now().isoformat())
            ))
            migrated += 1
        except Error as e:
            print(f"❌ Error migrating payment {payment_id}: {e}")
    
    print(f"✅ Migrated {migrated} payments")

def migrate_connection_history(cursor, history_file):
    """Migrate connection history from JSON to MySQL"""
    if not history_file.exists():
        print(f"⚠️  Connection history file not found: {history_file}")
        return
    
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    migrated = 0
    for entry in history:
        try:
            cursor.execute("""
                INSERT INTO connection_history (username, client_name, protocol, action, ip_address, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                entry.get('username'),
                entry.get('client_name'),
                entry.get('protocol'),
                entry.get('action', 'connect'),
                entry.get('ip_address'),
                entry.get('timestamp', datetime.now().isoformat())
            ))
            migrated += 1
        except Error as e:
            print(f"❌ Error migrating history entry: {e}")
    
    print(f"✅ Migrated {migrated} history entries")

def main():
    """Main migration function"""
    print("="*80)
    print("🔄 MySQL Migration Script")
    print("="*80)
    print()
    
    # Check database password
    if not DB_CONFIG['password']:
        print("❌ Error: MYSQL_PASSWORD environment variable not set")
        print("   Set it with: export MYSQL_PASSWORD='your-password'")
        sys.exit(1)
    
    try:
        # Connect to MySQL
        print("Connecting to MySQL...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to MySQL")
        
        # Create tables
        print("\nCreating tables...")
        create_tables(cursor)
        connection.commit()
        
        # Migrate data
        print("\nMigrating users...")
        migrate_users(cursor, USERS_FILE)
        connection.commit()
        
        print("\nMigrating clients...")
        migrate_clients(cursor, CLIENTS_FILE)
        connection.commit()
        
        print("\nMigrating payments...")
        migrate_payments(cursor, PAYMENT_REQUESTS_FILE)
        connection.commit()
        
        print("\nMigrating connection history...")
        migrate_connection_history(cursor, CONNECTION_HISTORY)
        connection.commit()
        
        print("\n" + "="*80)
        print("✅ Migration Complete!")
        print("="*80)
        print()
        print("Next steps:")
        print("1. Update app.py to use MySQL instead of JSON files")
        print("2. Test all functionality")
        print("3. Keep JSON files as backup")
        print("4. Remove JSON file reads once verified")
        
    except Error as e:
        print(f"❌ MySQL Error: {e}")
        sys.exit(1)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\n✅ MySQL connection closed")

if __name__ == '__main__':
    import os
    main()

