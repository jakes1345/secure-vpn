#!/bin/bash
# Setup Productivity Suite (Docs, Sheets, Slides)
# Google Workspace / Microsoft 365 alternative

set -e

echo "📝 Setting up Productivity Suite..."

# Install dependencies
apt-get update
apt-get install -y \
    python3-pip \
    python3-flask \
    python3-flask-cors \
    nodejs \
    npm

pip3 install \
    flask \
    flask-cors \
    python-docx \
    openpyxl \
    python-pptx \
    markdown \
    pdfkit

# Create productivity API
mkdir -p /opt/phazevpn-email/productivity-api
cat > /opt/phazevpn-email/productivity-api/app.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
PhazeVPN Productivity Suite API
Docs, Sheets, Slides (Google Workspace alternative)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

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
        return f(*args, **kwargs)
    return decorated

@app.route('/api/v1/productivity/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'PhazeVPN Productivity Suite',
        'features': ['docs', 'sheets', 'slides']
    })

@app.route('/api/v1/productivity/docs', methods=['GET'])
@require_auth
def list_docs():
    """List all documents"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    doc_type = request.args.get('type', 'doc')  # doc, sheet, slide
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM productivity_docs 
            WHERE user_email = %s AND doc_type = %s
            ORDER BY updated_at DESC
        """, (user_email, doc_type))
        docs = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({'documents': docs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/productivity/docs', methods=['POST'])
@require_auth
def create_doc():
    """Create new document"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    doc_type = data.get('type', 'doc')  # doc, sheet, slide
    doc_name = data.get('name', 'Untitled Document')
    
    # Default content based on type
    default_content = {
        'doc': {'blocks': [{'type': 'paragraph', 'text': ''}]},
        'sheet': {'cells': {}, 'rows': 100, 'cols': 26},
        'slide': {'slides': [{'content': ''}]}
    }
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO productivity_docs 
            (user_email, doc_type, doc_name, content)
            VALUES (%s, %s, %s, %s)
        """, (user_email, doc_type, doc_name, json.dumps(default_content.get(doc_type, {}))))
        db.commit()
        doc_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Document created',
            'doc_id': doc_id,
            'doc_name': doc_name
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/productivity/docs/<int:doc_id>', methods=['GET'])
@require_auth
def get_doc(doc_id):
    """Get document content"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM productivity_docs WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()
        cursor.close()
        db.close()
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        if isinstance(doc['content'], str):
            doc['content'] = json.loads(doc['content'])
        
        return jsonify(doc)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/productivity/docs/<int:doc_id>', methods=['PUT'])
@require_auth
def update_doc(doc_id):
    """Update document content"""
    data = request.json
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        updates = []
        values = []
        
        if 'name' in data:
            updates.append("doc_name = %s")
            values.append(data['name'])
        
        if 'content' in data:
            updates.append("content = %s")
            values.append(json.dumps(data['content']))
        
        if updates:
            values.append(doc_id)
            query = f"UPDATE productivity_docs SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            db.commit()
        
        cursor.close()
        db.close()
        
        return jsonify({'message': 'Document updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/productivity/docs/<int:doc_id>', methods=['DELETE'])
@require_auth
def delete_doc(doc_id):
    """Delete document"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM productivity_docs WHERE id = %s", (doc_id,))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'message': 'Document deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/productivity/docs/<int:doc_id>/share', methods=['POST'])
@require_auth
def share_doc(doc_id):
    """Share document with other users"""
    data = request.json
    shared_with = data.get('shared_with', [])  # List of emails
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE productivity_docs 
            SET is_shared = %s, shared_with = %s 
            WHERE id = %s
        """, (True, json.dumps(shared_with), doc_id))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'message': 'Document shared'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
PYTHON_EOF

chmod +x /opt/phazevpn-email/productivity-api/app.py

# Create systemd service
cat > /etc/systemd/system/phazevpn-productivity.service << 'SERVICE_EOF'
[Unit]
Description=PhazeVPN Productivity Suite API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-email/productivity-api
ExecStart=/usr/bin/python3 /opt/phazevpn-email/productivity-api/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable phazevpn-productivity
systemctl start phazevpn-productivity

# Configure firewall
ufw allow 5003/tcp comment 'Productivity Suite API'

echo "✅ Productivity Suite setup complete!"
echo "   - API: http://0.0.0.0:5003"
echo "   - Features: Docs, Sheets, Slides"
