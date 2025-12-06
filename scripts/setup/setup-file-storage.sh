#!/bin/bash
# Setup File Storage System (Google Drive-like)
# Provides cloud storage for users

set -e

echo "📁 Setting up File Storage System..."

# Install dependencies
apt-get update
apt-get install -y \
    python3-pip \
    python3-flask \
    python3-flask-cors \
    python3-pillow \
    python3-magic \
    nginx \
    sqlite3

pip3 install \
    flask \
    flask-cors \
    Pillow \
    python-magic \
    werkzeug \
    python-multipart

# Create storage structure
STORAGE_ROOT="/opt/phazevpn-email/storage"
mkdir -p ${STORAGE_ROOT}/{users,shared,trash,uploads,temp}

# Create file storage API
mkdir -p /opt/phazevpn-email/storage-api
cat > /opt/phazevpn-email/storage-api/app.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
PhazeVPN File Storage API
Google Drive-like cloud storage
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector
import os
import hashlib
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

STORAGE_ROOT = "/opt/phazevpn-email/storage"

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='mailuser',
        password='mailpass',
        database='mailserver'
    )

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401
        # TODO: Implement proper auth
        return f(*args, **kwargs)
    return decorated

@app.route('/api/v1/storage/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'PhazeVPN File Storage'})

@app.route('/api/v1/storage/files', methods=['GET'])
@require_auth
def list_files():
    """List files and folders"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    folder_id = request.args.get('folder_id', None)
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        if folder_id:
            cursor.execute("""
                SELECT * FROM file_storage 
                WHERE user_email = %s AND parent_folder_id = %s
                ORDER BY is_folder DESC, file_name ASC
            """, (user_email, folder_id))
        else:
            cursor.execute("""
                SELECT * FROM file_storage 
                WHERE user_email = %s AND parent_folder_id IS NULL
                ORDER BY is_folder DESC, file_name ASC
            """, (user_email,))
        
        files = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/storage/upload', methods=['POST'])
@require_auth
def upload_file():
    """Upload file"""
    user_email = request.form.get('user', 'admin@phazevpn.duckdns.org')
    folder_id = request.form.get('folder_id', None)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        user_dir = os.path.join(STORAGE_ROOT, 'users', user_email.replace('@', '_at_'))
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(filename)
        
        # Save to database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO file_storage 
            (user_email, file_name, file_path, file_size, mime_type, parent_folder_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_email, filename, file_path, file_size, mime_type, folder_id))
        db.commit()
        file_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'File uploaded',
            'file_id': file_id,
            'file_name': filename,
            'file_size': file_size
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/storage/files/<int:file_id>', methods=['GET'])
@require_auth
def download_file(file_id):
    """Download file"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM file_storage WHERE id = %s", (file_id,))
        file_data = cursor.fetchone()
        cursor.close()
        db.close()
        
        if not file_data:
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_data['file_path'],
            as_attachment=True,
            download_name=file_data['file_name']
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/storage/folders', methods=['POST'])
@require_auth
def create_folder():
    """Create folder"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    folder_name = data.get('name')
    parent_id = data.get('parent_id', None)
    
    if not folder_name:
        return jsonify({'error': 'Folder name required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO file_storage 
            (user_email, file_name, file_path, file_size, mime_type, is_folder, parent_folder_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_email, folder_name, '', 0, 'folder', True, parent_id))
        db.commit()
        folder_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Folder created',
            'folder_id': folder_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/storage/files/<int:file_id>', methods=['DELETE'])
@require_auth
def delete_file(file_id):
    """Delete file or folder"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM file_storage WHERE id = %s", (file_id,))
        file_data = cursor.fetchone()
        
        if not file_data:
            return jsonify({'error': 'File not found'}), 404
        
        # Move to trash or delete
        if not file_data['is_folder']:
            os.remove(file_data['file_path'])
        
        cursor.execute("DELETE FROM file_storage WHERE id = %s", (file_id,))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'message': 'File deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
PYTHON_EOF

chmod +x /opt/phazevpn-email/storage-api/app.py

# Create systemd service
cat > /etc/systemd/system/phazevpn-storage.service << 'SERVICE_EOF'
[Unit]
Description=PhazeVPN File Storage API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-email/storage-api
ExecStart=/usr/bin/python3 /opt/phazevpn-email/storage-api/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable phazevpn-storage
systemctl start phazevpn-storage

# Configure firewall
ufw allow 5002/tcp comment 'File Storage API'

echo "✅ File Storage System setup complete!"
echo "   - API: http://0.0.0.0:5002"
echo "   - Storage: /opt/phazevpn-email/storage"
