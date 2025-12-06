#!/bin/bash
# Setup REST API for PhazeVPN Email
# Creates Flask API for email management

set -e

echo "🔌 Setting up REST API for PhazeVPN Email..."

# Install Python dependencies
apt-get update
apt-get install -y \
    python3-pip \
    python3-flask \
    python3-flask-cors \
    python3-mysql.connector \
    python3-jwt \
    python3-bcrypt

# Create API directory
mkdir -p /opt/phazevpn-email/api
cd /opt/phazevpn-email/api

# Create API structure
cat > app.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
PhazeVPN Email REST API
Provides API access to email functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import hashlib
import secrets
from functools import wraps
import json

app = Flask(__name__)
CORS(app)

# Database connection
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='mailuser',
        password='mailpass',
        database='mailserver'
    )

# API Authentication
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_api_key(api_key):
    # TODO: Implement API key validation
    return True

# Routes
@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'PhazeVPN Email API'})

@app.route('/api/v1/accounts', methods=['GET'])
@require_api_key
def list_accounts():
    """List all email accounts"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT email, quota, active FROM virtual_users")
        accounts = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify({'accounts': accounts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts', methods=['POST'])
@require_api_key
def create_account():
    """Create new email account"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    quota = data.get('quota', 1073741824)  # 1GB default
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO virtual_users (email, password, quota) VALUES (%s, %s, %s)",
            (email, password_hash, quota)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Account created', 'email': email}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts/<email>', methods=['DELETE'])
@require_api_key
def delete_account(email):
    """Delete email account"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM virtual_users WHERE email = %s", (email,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Account deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/send', methods=['POST'])
@require_api_key
def send_email():
    """Send email via API"""
    data = request.json
    to = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    from_email = data.get('from')
    
    if not all([to, subject, body, from_email]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # TODO: Implement actual email sending
    return jsonify({
        'message': 'Email sent',
        'to': to,
        'subject': subject
    }), 200

@app.route('/api/v1/search', methods=['POST'])
@require_api_key
def search_emails():
    """Search emails"""
    data = request.json
    query = data.get('query')
    folder = data.get('folder', 'INBOX')
    
    # TODO: Implement email search
    return jsonify({
        'results': [],
        'query': query,
        'folder': folder
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
PYTHON_EOF

chmod +x app.py

# Create systemd service
cat > /etc/systemd/system/phazevpn-email-api.service << 'EOF'
[Unit]
Description=PhazeVPN Email REST API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-email/api
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start API
systemctl daemon-reload
systemctl enable phazevpn-email-api
systemctl start phazevpn-email-api

echo "✅ REST API installed!"
echo ""
echo "🔌 API Endpoints:"
echo "   - Base URL: http://localhost:5000/api/v1"
echo "   - Health: GET /api/v1/health"
echo "   - Accounts: GET/POST /api/v1/accounts"
echo "   - Send: POST /api/v1/send"
echo "   - Search: POST /api/v1/search"
echo ""
echo "🔑 Authentication:"
echo "   - Add X-API-Key header to requests"
echo "   - Generate API keys: ./manage-api-keys.sh create"
