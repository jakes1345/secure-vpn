#!/usr/bin/env python3
"""
PhazeVPN Extensibility API
Plugin system, API builder, marketplace, webhooks
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import json
import hashlib
import secrets
from datetime import datetime
import subprocess
import os

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
        # TODO: Implement proper auth
        return f(*args, **kwargs)
    return decorated

# ============================================
# PLUGIN SYSTEM
# ============================================

@app.route('/api/v1/extensibility/plugins', methods=['GET'])
@require_auth
def list_plugins():
    """List all plugins"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    plugin_type = request.args.get('type', None)
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        if plugin_type:
            cursor.execute("""
                SELECT * FROM user_plugins 
                WHERE user_email = %s AND plugin_type = %s
                ORDER BY created_at DESC
            """, (user_email, plugin_type))
        else:
            cursor.execute("""
                SELECT * FROM user_plugins 
                WHERE user_email = %s OR is_public = TRUE
                ORDER BY created_at DESC
            """, (user_email,))
        
        plugins = cursor.fetchall()
        
        # Parse JSON fields
        for p in plugins:
            if isinstance(p.get('config'), str):
                p['config'] = json.loads(p['config']) if p['config'] else {}
        
        cursor.close()
        db.close()
        
        return jsonify({'plugins': plugins})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/plugins', methods=['POST'])
@require_auth
def create_plugin():
    """Create new plugin/app"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    plugin_name = data.get('name')
    plugin_type = data.get('type', 'plugin')
    description = data.get('description', '')
    code = data.get('code', '')
    config = data.get('config', {})
    
    if not plugin_name:
        return jsonify({'error': 'Plugin name required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO user_plugins 
            (user_email, plugin_name, plugin_type, description, code, config)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_email, plugin_name, plugin_type, description, code, json.dumps(config)))
        db.commit()
        plugin_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Plugin created',
            'plugin_id': plugin_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/plugins/<int:plugin_id>', methods=['GET'])
@require_auth
def get_plugin(plugin_id):
    """Get plugin by ID"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_plugins WHERE id = %s", (plugin_id,))
        plugin = cursor.fetchone()
        
        if plugin and isinstance(plugin.get('config'), str):
            plugin['config'] = json.loads(plugin['config']) if plugin['config'] else {}
        
        cursor.close()
        db.close()
        
        if not plugin:
            return jsonify({'error': 'Plugin not found'}), 404
        
        return jsonify(plugin)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/plugins/<int:plugin_id>', methods=['PUT'])
@require_auth
def update_plugin(plugin_id):
    """Update plugin"""
    data = request.json
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        updates = []
        values = []
        
        if 'name' in data:
            updates.append("plugin_name = %s")
            values.append(data['name'])
        if 'description' in data:
            updates.append("description = %s")
            values.append(data['description'])
        if 'code' in data:
            updates.append("code = %s")
            values.append(data['code'])
        if 'config' in data:
            updates.append("config = %s")
            values.append(json.dumps(data['config']))
        if 'status' in data:
            updates.append("status = %s")
            values.append(data['status'])
        
        if updates:
            values.append(plugin_id)
            query = f"UPDATE user_plugins SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            db.commit()
        
        cursor.close()
        db.close()
        
        return jsonify({'message': 'Plugin updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# API BUILDER
# ============================================

@app.route('/api/v1/extensibility/endpoints', methods=['GET'])
@require_auth
def list_endpoints():
    """List user-created API endpoints"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM user_api_endpoints 
            WHERE user_email = %s
            ORDER BY created_at DESC
        """, (user_email,))
        endpoints = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({'endpoints': endpoints})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/endpoints', methods=['POST'])
@require_auth
def create_endpoint():
    """Create custom API endpoint"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    endpoint_name = data.get('name')
    endpoint_path = data.get('path')
    method = data.get('method', 'GET')
    handler_code = data.get('code', '')
    auth_required = data.get('auth_required', True)
    rate_limit = data.get('rate_limit', 100)
    
    if not endpoint_name or not endpoint_path:
        return jsonify({'error': 'Endpoint name and path required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO user_api_endpoints 
            (user_email, endpoint_name, endpoint_path, method, handler_code, auth_required, rate_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_email, endpoint_name, endpoint_path, method, handler_code, auth_required, rate_limit))
        db.commit()
        endpoint_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Endpoint created',
            'endpoint_id': endpoint_id,
            'url': f'/api/v1/extensibility/custom/{endpoint_path}'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/custom/<path:endpoint_path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def execute_custom_endpoint(endpoint_path):
    """Execute user-created API endpoint"""
    method = request.method
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM user_api_endpoints 
            WHERE endpoint_path = %s AND method = %s
        """, (endpoint_path, method))
        endpoint = cursor.fetchone()
        cursor.close()
        db.close()
        
        if not endpoint:
            return jsonify({'error': 'Endpoint not found'}), 404
        
        # Execute handler code (sandboxed)
        # In production, use proper sandboxing
        try:
            # Create execution context
            exec_globals = {
                'request': request,
                'jsonify': jsonify,
                'json': json,
                'datetime': datetime
            }
            
            # Execute code
            exec(endpoint['handler_code'], exec_globals)
            
            # Get result
            if 'result' in exec_globals:
                return exec_globals['result']
            else:
                return jsonify({'message': 'Endpoint executed', 'endpoint': endpoint_path})
        except Exception as e:
            return jsonify({'error': f'Execution error: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# WEBHOOKS
# ============================================

@app.route('/api/v1/extensibility/webhooks', methods=['GET'])
@require_auth
def list_webhooks():
    """List webhooks"""
    user_email = request.args.get('user', 'admin@phazevpn.duckdns.org')
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM webhooks 
            WHERE user_email = %s
            ORDER BY created_at DESC
        """, (user_email,))
        webhooks = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({'webhooks': webhooks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/webhooks', methods=['POST'])
@require_auth
def create_webhook():
    """Create webhook"""
    data = request.json
    user_email = data.get('user', 'admin@phazevpn.duckdns.org')
    webhook_name = data.get('name')
    webhook_url = data.get('url')
    event_type = data.get('event_type')
    
    if not webhook_name or not webhook_url or not event_type:
        return jsonify({'error': 'Name, URL, and event type required'}), 400
    
    # Generate secret
    secret = secrets.token_urlsafe(32)
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO webhooks 
            (user_email, webhook_name, webhook_url, event_type, secret)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_email, webhook_name, webhook_url, event_type, secret))
        db.commit()
        webhook_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'Webhook created',
            'webhook_id': webhook_id,
            'secret': secret
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/webhooks/<int:webhook_id>/trigger', methods=['POST'])
@require_auth
def trigger_webhook(webhook_id):
    """Manually trigger webhook"""
    data = request.json
    event_data = data.get('data', {})
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM webhooks WHERE id = %s", (webhook_id,))
        webhook = cursor.fetchone()
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        # Send webhook (in production, use async task queue)
        import requests
        try:
            response = requests.post(
                webhook['webhook_url'],
                json=event_data,
                headers={'X-Webhook-Secret': webhook['secret']},
                timeout=10
            )
            
            # Log event
            cursor.execute("""
                INSERT INTO webhook_events 
                (webhook_id, event_data, status, response_code, response_body)
                VALUES (%s, %s, %s, %s, %s)
            """, (webhook_id, json.dumps(event_data), 'sent', response.status_code, response.text))
            db.commit()
            
            return jsonify({
                'message': 'Webhook triggered',
                'status_code': response.status_code
            })
        except Exception as e:
            cursor.execute("""
                INSERT INTO webhook_events 
                (webhook_id, event_data, status)
                VALUES (%s, %s, 'failed')
            """, (webhook_id, json.dumps(event_data)))
            db.commit()
            
            return jsonify({'error': str(e)}), 500
        
        cursor.close()
        db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# MARKETPLACE
# ============================================

@app.route('/api/v1/extensibility/marketplace', methods=['GET'])
def list_marketplace():
    """List marketplace apps"""
    category = request.args.get('category', None)
    featured = request.args.get('featured', False)
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        if featured:
            cursor.execute("""
                SELECT p.*, m.category, m.price, m.is_featured
                FROM user_plugins p
                JOIN marketplace_apps m ON p.id = m.plugin_id
                WHERE p.is_public = TRUE AND p.status = 'active' AND m.is_featured = TRUE
                ORDER BY p.downloads DESC
            """)
        elif category:
            cursor.execute("""
                SELECT p.*, m.category, m.price, m.is_featured
                FROM user_plugins p
                JOIN marketplace_apps m ON p.id = m.plugin_id
                WHERE p.is_public = TRUE AND p.status = 'active' AND m.category = %s
                ORDER BY p.downloads DESC
            """, (category,))
        else:
            cursor.execute("""
                SELECT p.*, m.category, m.price, m.is_featured
                FROM user_plugins p
                JOIN marketplace_apps m ON p.id = m.plugin_id
                WHERE p.is_public = TRUE AND p.status = 'active'
                ORDER BY p.downloads DESC
            """)
        
        apps = cursor.fetchall()
        
        # Parse JSON
        for app in apps:
            if isinstance(app.get('config'), str):
                app['config'] = json.loads(app['config']) if app['config'] else {}
        
        cursor.close()
        db.close()
        
        return jsonify({'apps': apps})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/marketplace/<int:plugin_id>/publish', methods=['POST'])
@require_auth
def publish_to_marketplace(plugin_id):
    """Publish plugin to marketplace"""
    data = request.json
    category = data.get('category', 'general')
    price = data.get('price', 0.00)
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Update plugin to public
        cursor.execute("""
            UPDATE user_plugins 
            SET is_public = TRUE, status = 'active'
            WHERE id = %s
        """, (plugin_id,))
        
        # Add to marketplace
        cursor.execute("""
            INSERT INTO marketplace_apps (plugin_id, category, price)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE category = %s, price = %s
        """, (plugin_id, category, price, category, price))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'message': 'Published to marketplace'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/extensibility/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'PhazeVPN Extensibility API',
        'features': ['plugins', 'api-builder', 'webhooks', 'marketplace']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
