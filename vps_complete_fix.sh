#!/bin/bash
# Complete VPS Fix Script

echo "🔧 Fixing PhazeVPN VPS..."

# 1. Kill all old processes
echo "1. Stopping old services..."
pkill -9 -f "python3 app.py"
pkill -9 -f phazevpn-server
sleep 2

# 2. Fix Python environment
echo "2. Installing Python dependencies..."
cd /opt/phazevpn
source venv/bin/activate
pip install --upgrade pip
pip install flask flask-cors mysql-connector-python requests gunicorn
deactivate

# 3. Setup MySQL database
echo "3. Setting up database..."
mysql -u root -pJakes1328!@ << 'EOSQL'
CREATE DATABASE IF NOT EXISTS phazevpn_db;
USE phazevpn_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vpn_clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    client_name VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

GRANT ALL PRIVILEGES ON phazevpn_db.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
EOSQL

# 4. Start services properly
echo "4. Starting services..."

# VPN Server
cd /opt/phazevpn/phazevpn-protocol-go
nohup /usr/local/go/bin/go run main.go > /var/log/phazevpn.log 2>&1 &

# Web Portal
cd /opt/phaze-vpn/web-portal
nohup /opt/phazevpn/venv/bin/python3 app.py > /var/log/phazeweb.log 2>&1 &

# Email Service
cd /opt/phazevpn/email-service
nohup /opt/phazevpn/venv/bin/python3 app.py > /var/log/phazeemail.log 2>&1 &

sleep 3

echo "5. Verifying services..."
ps aux | grep -E "python3 app.py|phazevpn|go run" | grep -v grep

echo "✅ Fix complete!"
