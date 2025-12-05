#!/usr/bin/env python3
"""
Reset MySQL root password to match VPS password
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 RESETTING MYSQL ROOT PASSWORD")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Stop MySQL
    print("\n🛑 Stopping MySQL...")
    stdin, stdout, stderr = ssh.exec_command('systemctl stop mysql')
    time.sleep(2)
    
    # Start MySQL in safe mode
    print("🔓 Starting MySQL in safe mode...")
    stdin, stdout, stderr = ssh.exec_command('mysqld_safe --skip-grant-tables --skip-networking &')
    time.sleep(5)
    
    # Reset password
    print("🔑 Resetting password...")
    reset_sql = "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Jakes1328!@'; FLUSH PRIVILEGES;"
    stdin, stdout, stderr = ssh.exec_command(f"mysql -u root -e \"{reset_sql}\" 2>&1")
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if 'ERROR' not in output and 'ERROR' not in error:
        print("   ✅ Password reset!")
    else:
        print(f"   ⚠️  {output}{error}")
    
    # Kill safe mode
    print("\n🔄 Restarting MySQL normally...")
    stdin, stdout, stderr = ssh.exec_command('pkill mysqld_safe && sleep 2 && systemctl start mysql')
    time.sleep(3)
    
    # Test new password
    print("\n🧪 Testing new password...")
    stdin, stdout, stderr = ssh.exec_command('mysql -u root -pJakes1328!@ -e "SELECT 1;" 2>&1')
    test = stdout.read().decode()
    
    if 'ERROR' not in test:
        print("   ✅ MySQL password is now: Jakes1328!@")
        print("   ✅ Can now create database!")
        
        # Create database
        print("\n📦 Creating database...")
        stdin, stdout, stderr = ssh.exec_command('mysql -u root -pJakes1328!@ < /tmp/setup-db.sql 2>&1')
        output = stdout.read().decode()
        if 'ERROR' not in output:
            print("   ✅ Database created!")
        else:
            print(f"   ⚠️  {output}")
        
        # Create tables
        print("\n📋 Creating tables...")
        stdin, stdout, stderr = ssh.exec_command('mysql -u root -pJakes1328!@ < /tmp/create-tables.sql 2>&1')
        output = stdout.read().decode()
        if 'ERROR' not in output:
            print("   ✅ Tables created!")
        else:
            print(f"   ⚠️  {output}")
        
        # Verify
        print("\n✅ Verifying...")
        stdin, stdout, stderr = ssh.exec_command('mysql -u root -pJakes1328!@ -e "USE phazevpn; SHOW TABLES;" 2>&1')
        tables = stdout.read().decode()
        if 'users' in tables or 'payments' in tables:
            print(f"   ✅ Database verified!")
            print(f"   Tables: {tables.strip()}")
        else:
            print(f"   Tables: {tables}")
    else:
        print(f"   ❌ Password reset may have failed: {test}")
    
    ssh.close()

if __name__ == "__main__":
    main()

