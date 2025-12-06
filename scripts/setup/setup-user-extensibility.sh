#!/bin/bash
# Setup User Extensibility System
# Plugin system, API builder, marketplace, webhooks

set -e

echo "🔌 Setting up User Extensibility System..."

# Install dependencies
apt-get update
apt-get install -y \
    python3-pip \
    python3-flask \
    python3-flask-cors \
    python3-sqlalchemy \
    python3-jinja2 \
    nodejs \
    npm \
    redis-server

pip3 install \
    flask \
    flask-cors \
    sqlalchemy \
    redis \
    celery \
    python-jose \
    cryptography \
    requests

# Create directories
mkdir -p /opt/phazevpn-extensibility/{plugins,marketplace,webhooks,api-builder}
mkdir -p /opt/phazevpn-extensibility/plugins/{user-plugins,official-plugins}
mkdir -p /opt/phazevpn-extensibility/marketplace/{apps,reviews,ratings}
mkdir -p /opt/phazevpn-extensibility/webhooks/{endpoints,events,logs}

# Database setup
mysql -u root -pmailpass << 'SQL_EOF'
USE mailserver;

-- User plugins/apps
CREATE TABLE IF NOT EXISTS user_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    plugin_type ENUM('plugin', 'app', 'integration', 'webhook') NOT NULL,
    description TEXT,
    code TEXT,
    config JSON,
    version VARCHAR(20) DEFAULT '1.0.0',
    status ENUM('draft', 'active', 'paused', 'archived') DEFAULT 'draft',
    is_public BOOLEAN DEFAULT FALSE,
    is_official BOOLEAN DEFAULT FALSE,
    downloads INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Plugin permissions
CREATE TABLE IF NOT EXISTS plugin_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id INT NOT NULL,
    permission_type VARCHAR(50) NOT NULL,
    resource VARCHAR(100),
    action VARCHAR(50),
    FOREIGN KEY (plugin_id) REFERENCES user_plugins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Marketplace apps
CREATE TABLE IF NOT EXISTS marketplace_apps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id INT NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) DEFAULT 0.00,
    is_featured BOOLEAN DEFAULT FALSE,
    featured_until DATE,
    FOREIGN KEY (plugin_id) REFERENCES user_plugins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- App reviews
CREATE TABLE IF NOT EXISTS app_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id INT NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plugin_id) REFERENCES user_plugins(id) ON DELETE CASCADE,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Webhooks
CREATE TABLE IF NOT EXISTS webhooks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    webhook_name VARCHAR(100) NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Webhook events log
CREATE TABLE IF NOT EXISTS webhook_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    webhook_id INT NOT NULL,
    event_data JSON,
    status ENUM('pending', 'sent', 'failed') DEFAULT 'pending',
    response_code INT,
    response_body TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- API endpoints (user-created)
CREATE TABLE IF NOT EXISTS user_api_endpoints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    endpoint_name VARCHAR(100) NOT NULL,
    endpoint_path VARCHAR(200) NOT NULL,
    method ENUM('GET', 'POST', 'PUT', 'DELETE', 'PATCH') NOT NULL,
    handler_code TEXT,
    auth_required BOOLEAN DEFAULT TRUE,
    rate_limit INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE,
    UNIQUE KEY unique_endpoint (endpoint_path, method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SQL_EOF

echo "✅ Database schema created"

# Set permissions
chown -R mailuser:mailuser /opt/phazevpn-extensibility
chmod -R 755 /opt/phazevpn-extensibility

echo "✅ User Extensibility System database setup complete!"
