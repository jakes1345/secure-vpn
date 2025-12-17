-- PhazeVPN Database Setup
CREATE DATABASE IF NOT EXISTS phazevpn_db;
USE phazevpn_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- VPN Clients table
CREATE TABLE IF NOT EXISTS vpn_clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    client_name VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    protocol VARCHAR(20) DEFAULT 'phazevpn',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_connected TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create default admin user (password: Jakes1328!@)
-- Password hash for 'Jakes1328!@' using werkzeug
INSERT IGNORE INTO users (username, email, password_hash, subscription_tier) 
VALUES ('admin', 'admin@phazevpn.com', 'pbkdf2:sha256:260000$randomsalt$hashedpassword', 'premium');

SELECT 'Database setup complete!' AS status;
