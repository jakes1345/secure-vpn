#!/bin/bash
# Fix MySQL and Setup Database

echo "🔧 Fixing MySQL..."

# Stop MySQL
sudo systemctl stop mysql

# Start MySQL in safe mode (no password required)
sudo mkdir -p /var/run/mysqld
sudo chown mysql:mysql /var/run/mysqld
sudo mysqld_safe --skip-grant-tables &
sleep 5

# Reset root password
sudo mysql -u root << 'EOF'
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Jakes1328!@';
FLUSH PRIVILEGES;
EOF

# Stop safe mode
sudo pkill mysqld
sleep 3

# Start MySQL normally
sudo systemctl start mysql
sleep 2

# Create database and tables
sudo mysql -u root -pJakes1328!@ < /tmp/setup_database.sql

echo "✅ MySQL fixed and database created!"
