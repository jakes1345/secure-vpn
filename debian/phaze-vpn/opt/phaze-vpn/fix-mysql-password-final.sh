#!/bin/bash
# Reset MySQL root password to Jakes1328!@

echo "🔧 Resetting MySQL root password..."

# Create socket directory
mkdir -p /var/run/mysqld
chown mysql:mysql /var/run/mysqld

# Stop MySQL
systemctl stop mysql
sleep 2

# Start in safe mode
mysqld_safe --skip-grant-tables --skip-networking --socket=/var/run/mysqld/mysqld.sock &
sleep 5

# Reset password
mysql --socket=/var/run/mysqld/mysqld.sock -u root << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Jakes1328!@';
FLUSH PRIVILEGES;
EOF

# Kill safe mode
pkill -9 mysqld
sleep 2

# Start MySQL normally
systemctl start mysql
sleep 3

# Test
mysql -u root -pJakes1328!@ -e "SELECT 1;" && echo "✅ Password reset successful!" || echo "❌ Password reset failed"

# Create database
mysql -u root -pJakes1328!@ < /tmp/setup-db.sql && echo "✅ Database created!" || echo "❌ Database creation failed"

# Create tables
mysql -u root -pJakes1328!@ < /tmp/create-tables.sql && echo "✅ Tables created!" || echo "❌ Table creation failed"

echo "✅ Done! MySQL root password is now: Jakes1328!@"

