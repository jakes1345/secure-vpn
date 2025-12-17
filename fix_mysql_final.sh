#!/bin/bash
# Final MySQL Fix Script

echo "🔧 Final MySQL Fix..."

# Stop MySQL
systemctl stop mysql || true
pkill -9 mysqld || true

# Prepare socket dir
mkdir -p /var/run/mysqld
chown mysql:mysql /var/run/mysqld
chmod 755 /var/run/mysqld

# Start in safe mode
mysqld_safe --skip-grant-tables --skip-networking &
PID=$!
echo "Waiting for MySQL safe mode..."
sleep 10

# Reset password
echo "Resetting root password..."
mysql -u root <<EOF
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Jakes1328!@';
FLUSH PRIVILEGES;
EOF

# Kill safe mode
echo "Stopping safe mode..."
kill $PID
pkill -9 mysqld || true
sleep 5

# Start normally
echo "Starting MySQL normally..."
systemctl start mysql
sleep 5

# Check status
systemctl status mysql --no-pager

# Run database setup
echo "Running database setup..."
mysql -u root -pJakes1328!@ < /tmp/setup_database.sql

echo "✅ MySQL Fix Complete"
