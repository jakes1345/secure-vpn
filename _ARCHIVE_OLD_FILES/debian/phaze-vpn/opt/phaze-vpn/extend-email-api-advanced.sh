#!/bin/bash
# Extend Email API with Advanced Features
# Search, Labels, Filters, Templates

set -e

echo "🔧 Extending Email API with Advanced Features..."

# Install search dependencies
pip3 install whoosh

# Backup existing API
cp /opt/phazevpn-email/api/app.py /opt/phazevpn-email/api/app.py.backup

# Extend API with advanced features
cat >> /opt/phazevpn-email/api/app.py << 'PYTHON_EOF'

# ============================================
# ADVANCED EMAIL FEATURES
# ============================================

from whoosh.index import create_index, open_dir
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.qparser import QueryParser
import os

# Search index setup
SEARCH_INDEX_DIR = "/opt/phazevpn-email/search-index"
os.makedirs(SEARCH_INDEX_DIR, exist_ok=True)

def get_search_index(user_email):
    """Get or create search index for user"""
    user_index_dir = os.path.join(SEARCH_INDEX_DIR, user_email.replace('@', '_at_'))
    os.makedirs(user_index_dir, exist_ok=True)
    
    schema = Schema(
        email_id=ID(stored=True),
        subject=TEXT(stored=True),
        body=TEXT(stored=True),
        from_email=TEXT(stored=True),
        to_email=TEXT(stored=True),
        date=DATETIME(stored=True)
    )
    
    if not os.path.exists(os.path.join(user_index_dir, "_MAIN_0.toc")):
        ix = create_index(user_index_dir, schema)
    else:
        ix = open_dir(user_index_dir)
    
    return ix

@app.route('/api/v1/labels', methods=['GET'])
@require_api_key
def list_labels():
    """List all labels for user"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM email_labels 
            WHERE user_email = %s 
            ORDER BY label_name ASC
        """, (user_email,))
        labels = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({'labels': labels})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/labels', methods=['POST'])
@require_api_key
def create_label():
    """Create new label"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    label_name = data.get('name')
    color = data.get('color', '#4285f4')
    
    if not label_name:
        return jsonify({'error': 'Label name required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO email_labels (user_email, label_name, color)
            VALUES (%s, %s, %s)
        """, (user_email, label_name, color))
        db.commit()
        label_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Label created',
            'label_id': label_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/emails/<email_id>/labels', methods=['POST'])
@require_api_key
def add_label_to_email(email_id):
    """Add label to email"""
    data = request.json
    label_id = data.get('label_id')
    
    if not label_id:
        return jsonify({'error': 'Label ID required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT IGNORE INTO email_label_map (email_id, label_id)
            VALUES (%s, %s)
        """, (email_id, label_id))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'message': 'Label added to email'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/filters', methods=['GET'])
@require_api_key
def list_filters():
    """List all filters for user"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM email_filters 
            WHERE user_email = %s 
            ORDER BY priority DESC, created_at DESC
        """, (user_email,))
        filters = cursor.fetchall()
        
        # Parse JSON fields
        for f in filters:
            if isinstance(f['conditions'], str):
                f['conditions'] = json.loads(f['conditions'])
            if isinstance(f['actions'], str):
                f['actions'] = json.loads(f['actions'])
        
        cursor.close()
        db.close()
        
        return jsonify({'filters': filters})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/filters', methods=['POST'])
@require_api_key
def create_filter():
    """Create new email filter"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    filter_name = data.get('name')
    conditions = data.get('conditions', {})
    actions = data.get('actions', {})
    priority = data.get('priority', 0)
    
    if not filter_name:
        return jsonify({'error': 'Filter name required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO email_filters 
            (user_email, filter_name, conditions, actions, priority)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_email, filter_name, json.dumps(conditions), json.dumps(actions), priority))
        db.commit()
        filter_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Filter created',
            'filter_id': filter_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/templates', methods=['GET'])
@require_api_key
def list_templates():
    """List all email templates"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM email_templates 
            WHERE user_email = %s 
            ORDER BY updated_at DESC
        """, (user_email,))
        templates = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({'templates': templates})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/templates', methods=['POST'])
@require_api_key
def create_template():
    """Create email template"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    template_name = data.get('name')
    subject = data.get('subject', '')
    body = data.get('body', '')
    variables = data.get('variables', {})
    
    if not template_name:
        return jsonify({'error': 'Template name required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO email_templates 
            (user_email, template_name, subject, body, variables)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_email, template_name, subject, body, json.dumps(variables)))
        db.commit()
        template_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Template created',
            'template_id': template_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/templates/<int:template_id>', methods=['GET'])
@require_api_key
def get_template(template_id):
    """Get template by ID"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM email_templates WHERE id = %s", (template_id,))
        template = cursor.fetchone()
        
        if template and isinstance(template['variables'], str):
            template['variables'] = json.loads(template['variables'])
        
        cursor.close()
        db.close()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify(template)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/search', methods=['POST'])
@require_api_key
def advanced_search():
    """Advanced email search with full-text indexing"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    query = data.get('query', '')
    limit = data.get('limit', 50)
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    try:
        # Use Whoosh for full-text search
        ix = get_search_index(user_email)
        with ix.searcher() as searcher:
            query_parser = QueryParser("body", ix.schema)
            parsed_query = query_parser.parse(query)
            results = searcher.search(parsed_query, limit=limit)
            
            emails = []
            for result in results:
                emails.append({
                    'email_id': result['email_id'],
                    'subject': result['subject'],
                    'from': result['from_email'],
                    'to': result['to_email'],
                    'date': result['date'],
                    'snippet': result.highlights("body", top=1) or result['body'][:200]
                })
            
            return jsonify({
                'results': emails,
                'count': len(emails),
                'query': query
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

PYTHON_EOF

# Restart API
systemctl restart phazevpn-email-api

echo "✅ Email API extended with advanced features!"
echo "   - Labels (Gmail-style)"
echo "   - Filters (automated actions)"
echo "   - Templates (reusable emails)"
echo "   - Advanced Search (full-text)"
