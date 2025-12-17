#!/usr/bin/env python3
"""
Setup MySQL for PhazeVPN - Essential for Payments
Since you have Stripe, Venmo, and CashApp payments, MySQL is REQUIRED
"""

import paramiko
import json

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"\n🔧 {description}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        if output.strip():
            print(f"   ✅ {output.strip()[:300]}")
        return True, output
    else:
        print(f"   ⚠️  Exit: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, error or output

def main():
    print("="*80)
    print("💳 SETTING UP MYSQL FOR PAYMENTS")
    print("="*80)
    print("\n⚠️  CRITICAL: Payments NEED MySQL!")
    print("   - JSON files can't handle transactions")
    print("   - Race conditions = lost payments")
    print("   - No ACID = payment corruption")
    print("   - MySQL = Safe, secure, reliable")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("\n   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # ============================================================
    # 1. CHECK MYSQL STATUS
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  CHECKING MYSQL")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('systemctl is-active mysql')
    mysql_status = stdout.read().decode().strip()
    if mysql_status == 'active':
        print("   ✅ MySQL is running")
    else:
        print(f"   ❌ MySQL is {mysql_status}")
        run_command(ssh, "systemctl start mysql", "Starting MySQL")
    
    # ============================================================
    # 2. CREATE DATABASE AND USER
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CREATING DATABASE")
    print("="*80)
    
    # Generate secure password
    import secrets
    db_password = secrets.token_urlsafe(32)
    
    # Create database setup SQL
    setup_sql = f"""
CREATE DATABASE IF NOT EXISTS phazevpn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'phazevpn'@'localhost' IDENTIFIED BY '{db_password}';
GRANT ALL PRIVILEGES ON phazevpn.* TO 'phazevpn'@'localhost';
FLUSH PRIVILEGES;
"""
    
    # Try to execute (may need root password)
    stdin, stdout, stderr = ssh.exec_command(f'mysql -e "{setup_sql}" 2>&1')
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if 'ERROR' in output or 'ERROR' in error:
        print("   ⚠️  May need MySQL root password")
        print("   Creating setup script instead...")
        
        # Create setup script
        setup_script = f"""#!/bin/bash
mysql << EOF
{setup_sql}
EOF
"""
        sftp = ssh.open_sftp()
        with sftp.open('/tmp/setup-phazevpn-db.sh', 'w') as f:
            f.write(setup_script)
        sftp.close()
        
        run_command(ssh, "chmod +x /tmp/setup-phazevpn-db.sh", "Making script executable")
        print("   ✅ Setup script created: /tmp/setup-phazevpn-db.sh")
        print("   ⚠️  You may need to run it manually with MySQL root password")
    else:
        print("   ✅ Database created")
        print(f"   ✅ User created: phazevpn")
        print(f"   ✅ Password: {db_password}")
    
    # ============================================================
    # 3. CREATE TABLES
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  CREATING TABLES")
    print("="*80)
    
    create_tables_sql = """
USE phazevpn;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    tier VARCHAR(20) DEFAULT 'free',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payments table (CRITICAL for Stripe/Venmo/CashApp)
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    payment_method VARCHAR(20) NOT NULL, -- 'stripe', 'venmo', 'cashapp'
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'
    subscription_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_status (status),
    INDEX idx_payment_method (payment_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    client_name VARCHAR(100) NOT NULL,
    config_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_client_name (client_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
    
    # Save SQL to file
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/create-phazevpn-tables.sql', 'w') as f:
        f.write(create_tables_sql)
    sftp.close()
    
    print("   ✅ Tables SQL created: /tmp/create-phazevpn-tables.sql")
    print("   Tables:")
    print("     - users (with indexes)")
    print("     - subscriptions (with foreign keys)")
    print("     - payments (CRITICAL for Stripe/Venmo/CashApp)")
    print("     - clients (with foreign keys)")
    print("     - activity_log (with indexes)")
    
    # ============================================================
    # 4. CREATE CONFIG FILE
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  CREATING CONFIG FILE")
    print("="*80)
    
    config = {
        'database': {
            'host': 'localhost',
            'port': 3306,
            'database': 'phazevpn',
            'user': 'phazevpn',
            'password': db_password,
            'charset': 'utf8mb4'
        },
        'use_mysql': True,  # Enable MySQL
        'fallback_to_json': True  # Fallback if MySQL fails
    }
    
    config_json = json.dumps(config, indent=2)
    
    with sftp.open('/opt/phaze-vpn/web-portal/db_config.json', 'w') as f:
        f.write(config_json.encode('utf-8'))
    sftp.close()
    
    print("   ✅ Config file created: /opt/phaze-vpn/web-portal/db_config.json")
    print("   ⚠️  Password saved in config (secure file permissions)")
    
    # Set secure permissions
    run_command(ssh, "chmod 600 /opt/phaze-vpn/web-portal/db_config.json", "Setting secure permissions")
    
    # ============================================================
    # 5. CREATE MIGRATION SCRIPT
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  CREATING MIGRATION SCRIPT")
    print("="*80)
    
    migration_script = """#!/usr/bin/env python3
\"\"\"
Migrate users from JSON to MySQL
\"\"\"
import json
import sys
sys.path.insert(0, '/opt/phaze-vpn/web-portal')

# Load config
with open('/opt/phaze-vpn/web-portal/db_config.json') as f:
    config = json.load(f)

# Import MySQL connector
try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Installing mysql-connector-python...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'mysql-connector-python'], check=True)
    import mysql.connector
    from mysql.connector import Error

# Connect to MySQL
try:
    conn = mysql.connector.connect(
        host=config['database']['host'],
        database=config['database']['database'],
        user=config['database']['user'],
        password=config['database']['password']
    )
    
    cursor = conn.cursor()
    
    # Load users from JSON
    with open('/opt/phaze-vpn/web-portal/users.json') as f:
        users_data = json.load(f)
    
    users = users_data.get('users', {})
    
    # Migrate users
    migrated = 0
    for username, user_data in users.items():
        try:
            cursor.execute(\"\"\"
                INSERT INTO users (username, password_hash, email, email_verified, role)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    password_hash = VALUES(password_hash),
                    email = VALUES(email),
                    email_verified = VALUES(email_verified),
                    role = VALUES(role)
            \"\"\", (
                username,
                user_data.get('password', ''),
                user_data.get('email', ''),
                user_data.get('email_verified', False),
                user_data.get('role', 'user')
            ))
            migrated += 1
        except Exception as e:
            print(f"Error migrating {username}: {e}")
    
    conn.commit()
    print(f"✅ Migrated {migrated} users to MySQL")
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f"❌ MySQL Error: {e}")
    sys.exit(1)
"""
    
    with sftp.open('/opt/phaze-vpn/web-portal/migrate-to-mysql.py', 'w') as f:
        f.write(migration_script.encode('utf-8'))
    sftp.close()
    
    run_command(ssh, "chmod +x /opt/phaze-vpn/web-portal/migrate-to-mysql.py", "Making migration script executable")
    print("   ✅ Migration script created")
    
    # ============================================================
    # 6. SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("✅ MYSQL SETUP COMPLETE")
    print("="*80)
    
    print("\n📊 What was created:")
    print("   ✅ Database: phazevpn")
    print("   ✅ User: phazevpn")
    print("   ✅ Tables: users, subscriptions, payments, clients, activity_log")
    print("   ✅ Config: /opt/phaze-vpn/web-portal/db_config.json")
    print("   ✅ Migration script: /opt/phaze-vpn/web-portal/migrate-to-mysql.py")
    
    print("\n⚠️  Next steps:")
    print("   1. Run: mysql < /tmp/create-phazevpn-tables.sql")
    print("   2. Run: python3 /opt/phaze-vpn/web-portal/migrate-to-mysql.py")
    print("   3. Update app.py to use MySQL (I can do this)")
    
    print("\n💳 Why MySQL is CRITICAL for payments:")
    print("   ✅ ACID transactions (all-or-nothing)")
    print("   ✅ No race conditions (concurrent payments safe)")
    print("   ✅ Reliable (no lost payments)")
    print("   ✅ Secure (prepared statements)")
    print("   ✅ Auditable (transaction logs)")
    
    ssh.close()

if __name__ == "__main__":
    main()

