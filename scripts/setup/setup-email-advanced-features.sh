#!/bin/bash
# Setup Advanced Email Features
# Labels, Filters, Templates, Advanced Search, File Storage, Productivity Suite

set -e

echo "🚀 Setting up Advanced Email Features for PhazeVPN..."

# Install dependencies
apt-get update
apt-get install -y \
    python3-pip \
    python3-mysql.connector \
    python3-whoosh \
    python3-pillow \
    python3-pdf2 \
    python3-docx \
    python3-openpyxl \
    python3-flask \
    python3-flask-cors \
    sqlite3 \
    nginx

pip3 install --upgrade pip
pip3 install \
    whoosh \
    Pillow \
    PyPDF2 \
    python-docx \
    openpyxl \
    flask \
    flask-cors \
    werkzeug \
    python-magic

# Create directories
mkdir -p /opt/phazevpn-email/{storage,search-index,productivity}
mkdir -p /opt/phazevpn-email/storage/{users,shared,trash}
mkdir -p /opt/phazevpn-email/productivity/{docs,sheets,slides}

# Database setup
mysql -u root -pmailpass << 'SQL_EOF'
USE mailserver;

-- Labels table
CREATE TABLE IF NOT EXISTS email_labels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    label_name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#4285f4',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_label (user_email, label_name),
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Email labels junction table
CREATE TABLE IF NOT EXISTS email_label_map (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_id VARCHAR(255) NOT NULL,
    label_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_email_label (email_id, label_id),
    FOREIGN KEY (label_id) REFERENCES email_labels(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Filters table
CREATE TABLE IF NOT EXISTS email_filters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    filter_name VARCHAR(100) NOT NULL,
    conditions JSON NOT NULL,
    actions JSON NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    subject VARCHAR(500),
    body TEXT,
    variables JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- File storage table
CREATE TABLE IF NOT EXISTS file_storage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    parent_folder_id INT DEFAULT NULL,
    is_folder BOOLEAN DEFAULT FALSE,
    is_shared BOOLEAN DEFAULT FALSE,
    shared_with JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE,
    FOREIGN KEY (parent_folder_id) REFERENCES file_storage(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Search index metadata
CREATE TABLE IF NOT EXISTS search_index_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    index_version INT DEFAULT 1,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Productivity documents
CREATE TABLE IF NOT EXISTS productivity_docs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    doc_type ENUM('doc', 'sheet', 'slide') NOT NULL,
    doc_name VARCHAR(255) NOT NULL,
    content JSON,
    file_path VARCHAR(500),
    is_shared BOOLEAN DEFAULT FALSE,
    shared_with JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email) REFERENCES virtual_users(email) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SQL_EOF

echo "✅ Database schema created"

# Set permissions
chown -R mailuser:mailuser /opt/phazevpn-email
chmod -R 755 /opt/phazevpn-email

echo "✅ Advanced Email Features database setup complete!"
echo ""
echo "📋 Created tables:"
echo "   - email_labels (Gmail-style labels)"
echo "   - email_label_map (email-label relationships)"
echo "   - email_filters (automated email filtering)"
echo "   - email_templates (reusable email templates)"
echo "   - file_storage (Google Drive-like storage)"
echo "   - search_index_metadata (search optimization)"
echo "   - productivity_docs (docs, sheets, slides)"
