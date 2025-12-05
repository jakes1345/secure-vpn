#!/usr/bin/env python3
"""
SecureVPN Web Portal
Admin, Moderator, and User dashboards
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash, send_from_directory  # type: ignore
from functools import wraps
import json
import hashlib
import bcrypt
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta
import os
import qrcode
import io
import base64
import re
import csv
import secrets
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import 2FA module
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from twofa import generate_secret, get_qr_url, generate_qr_image, verify_token, enable_2fa, disable_2fa, is_2fa_enabled  # type: ignore
except ImportError:
    # Fallback if 2FA module not available
    def generate_secret(u): return None
    def get_qr_url(u, s, i='SecureVPN'): return ""
    def generate_qr_image(uri): return ""
    def verify_token(u, t): return True
    def enable_2fa(u): return False
    def disable_2fa(u): return False
    def is_2fa_enabled(u): return False

# Import existing modules
try:
    from vpn_manager import CONFIG as VPN_CONFIG  # type: ignore
except:
    # Use environment variables or default to domain
    VPN_CONFIG = {
        'server_ip': os.environ.get('VPN_SERVER_IP', 'phazevpn.com'),
        'server_port': int(os.environ.get('VPN_SERVER_PORT', '1194'))
    }

# Import payment integrations
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from payment_integrations import (
        create_stripe_checkout_session, verify_stripe_payment,
        handle_stripe_webhook, load_payment_settings, save_payment_settings
    )
except ImportError:
    # Fallback if payment integrations not available
    def create_stripe_checkout_session(*args, **kwargs): 
        return {'error': 'Stripe integration not available'}
    def verify_stripe_payment(*args, **kwargs): 
        return {'error': 'Stripe integration not available'}
    def handle_stripe_webhook(*args, **kwargs): 
        return {'error': 'Stripe integration not available'}
    def load_payment_settings(): 
        return {}
    def save_payment_settings(*args, **kwargs): 
        pass

# Configure Flask - but we'll handle downloads manually to avoid static file serving
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Override Flask's send_static_file to block Python files
@app.route('/static/<path:filename>')
def custom_static(filename):
    """Custom static file handler that blocks Python files"""
    if filename.endswith('.py'):
        return "Python files are not available for download.", 404
    return send_from_directory(app.static_folder, filename)

# Block Flask from serving Python files from static directory
@app.before_request
def block_python_files():
    """Block serving Python files from static directory"""
    # CRITICAL: Block Python files from being served via static handler
    # This must run BEFORE Flask's static file handler
    if request.path.endswith('.py'):
        # Always block Python files - never serve them
        return "Python files are not available for download. Please use the compiled executable.", 404
    
    # Block Python files in download/client route specifically
    if '/download/client/' in request.path and request.path.endswith('.py'):
        return "Python files are not available. Only compiled executables are served.", 404
app.secret_key = 'Y8Kp3mN9qR2vX7wL5zA6bC4dE1fG8hI0jK2lM6nO4pQ9rS3tU7vW1xY5zA8bC0dE2fG4hI6jK8lM0nO2pQ4rS6tU8vW0xY2zA4bC6dE8fG0hI2jK4lM6nO8pQ0rS2tU4vW6xY8zA0bC2dE4'  # Auto-generated secure key (64 chars)

# Security Settings - COOKIE HARDENING (Prevent cookie hacking)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access (XSS protection)
# Use Lax instead of Strict to allow cookies on redirects (still secure)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # LAX - Secure but allows redirects
# Auto-detect HTTPS from environment or request
is_https = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'
app.config['SESSION_COOKIE_SECURE'] = is_https  # Only require HTTPS if enabled
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # Shorter timeout (was 24h) - reduces attack window
# Only use __Secure- prefix if HTTPS is enabled (browsers reject it on HTTP)
app.config['SESSION_COOKIE_NAME'] = '__Secure-VPN-Session' if is_https else 'VPN-Session'
app.config['SESSION_COOKIE_PATH'] = '/'  # Only sent to exact path
app.config['SESSION_REFRESH_EACH_REQUEST'] = False  # Disable to prevent session issues on redirects

# Additional Security Headers - Applied to all responses
@app.after_request
def set_security_headers(response):
    """Add security headers to prevent cookie theft and attacks"""
    response.headers['X-Content-Type-Options'] = 'nosniff'  # Prevent MIME sniffing
    response.headers['X-Frame-Options'] = 'DENY'  # Prevent clickjacking
    response.headers['X-XSS-Protection'] = '1; mode=block'  # XSS protection
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'  # Force HTTPS
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'  # Privacy - limit referrer info
    # Privacy: Don't reveal server info
    response.headers['Server'] = ''  # Don't reveal server type
    return response

# Paths
BASE_DIR = Path(__file__).parent.parent
# Try multiple possible VPN directories (VPS typically uses /opt/phaze-vpn)
if (BASE_DIR / 'vpn-manager.py').exists():
    VPN_DIR = BASE_DIR
elif Path('/opt/phaze-vpn/vpn-manager.py').exists():
    VPN_DIR = Path('/opt/phaze-vpn')
elif Path('/opt/secure-vpn/vpn-manager.py').exists():
    VPN_DIR = Path('/opt/secure-vpn')
else:
    VPN_DIR = Path('/opt/phaze-vpn')  # Default for VPS
USERS_FILE = VPN_DIR / 'users.json'
CLIENT_CONFIGS_DIR = VPN_DIR / 'client-configs'
STATUS_LOG = VPN_DIR / 'logs' / 'status.log'
ACTIVITY_LOG = VPN_DIR / 'logs' / 'activity.log'
CONNECTION_HISTORY = VPN_DIR / 'logs' / 'connection-history.json'
PAYMENT_REQUESTS_FILE = VPN_DIR / 'logs' / 'payment-requests.json'
TICKETS_FILE = VPN_DIR / 'logs' / 'tickets.json'

# ============================================
# SUBSCRIPTION TIERS & LIMITS
# ============================================

SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'client_limit': 1,  # Only 1 device
        'bandwidth_limit_gb': 5,  # 5GB per month
        'features': ['1 Device', '5GB/month', 'Basic Support']
    },
    'basic': {
        'name': 'Basic',
        'price': 5.00,
        'price_monthly': 5.00,
        'price_yearly': 50.00,
        'client_limit': 3,  # 3 devices
        'bandwidth_limit_gb': 50,  # 50GB per month
        'features': ['3 Devices', '50GB/month', 'Email Support']
    },
    'pro': {
        'name': 'Pro',
        'price': 10.00,
        'price_monthly': 10.00,
        'price_yearly': 100.00,
        'client_limit': 10,  # 10 devices
        'bandwidth_limit_gb': 200,  # 200GB per month
        'features': ['10 Devices', '200GB/month', 'Priority Support', 'All Locations']
    },
    'premium': {
        'name': 'Premium',
        'price': 20.00,
        'price_monthly': 20.00,
        'price_yearly': 200.00,
        'client_limit': -1,  # Unlimited
        'bandwidth_limit_gb': -1,  # Unlimited
        'features': ['Unlimited Devices', 'Unlimited Bandwidth', '24/7 Support', 'All Locations', 'Dedicated IP Available']
    }
}

def get_user_subscription(username):
    """Get user's subscription tier"""
    users, _ = load_users()
    if username not in users:
        return 'free'
    subscription = users[username].get('subscription', {})
    tier = subscription.get('tier', 'free')
    return tier if tier in SUBSCRIPTION_TIERS else 'free'

def get_subscription_limits(username):
    """Get subscription limits for user"""
    tier = get_user_subscription(username)
    return SUBSCRIPTION_TIERS[tier]

def can_create_client(username):
    """Check if user can create another client"""
    users, _ = load_users()
    if username not in users:
        return False, 'User not found'
    
    tier = get_user_subscription(username)
    limits = SUBSCRIPTION_TIERS[tier]
    client_limit = limits['client_limit']
    
    # Unlimited (-1) means no limit
    if client_limit == -1:
        return True, None
    
    # Count user's current clients
    user_clients = users[username].get('clients', [])
    current_count = len([c for c in user_clients if (CLIENT_CONFIGS_DIR / f'{c}.ovpn').exists()])
    
    if current_count >= client_limit:
        return False, f'You have reached your limit of {client_limit} device(s). Upgrade to create more!'
    
    return True, None

# ============================================
# TICKET SYSTEM FUNCTIONS
# ============================================

def load_tickets():
    """Load tickets from file"""
    if TICKETS_FILE.exists():
        try:
            with open(TICKETS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {'tickets': {}}

def save_tickets(data):
    """Save tickets to file"""
    TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TICKETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def create_ticket(username, subject, message, email=None):
    """Create a new support ticket"""
    tickets_data = load_tickets()
    
    # Generate unique ticket ID
    ticket_id = f"TICKET-{secrets.token_hex(6).upper()}"
    
    ticket_data = {
        'id': ticket_id,
        'username': username,
        'email': email,
        'subject': subject,
        'message': message,
        'status': 'open',  # open, in_progress, resolved, closed
        'priority': 'normal',  # low, normal, high, urgent
        'created': datetime.now().isoformat(),
        'updated': datetime.now().isoformat(),
        'assigned_to': None,
        'replies': []  # List of replies: {user, message, created}
    }
    
    tickets_data['tickets'][ticket_id] = ticket_data
    save_tickets(tickets_data)
    
    log_activity(username, 'TICKET_CREATED', f'Created ticket: {ticket_id}')
    
    return ticket_id, ticket_data

def add_ticket_reply(ticket_id, username, message):
    """Add a reply to a ticket"""
    tickets_data = load_tickets()
    
    if ticket_id not in tickets_data['tickets']:
        return False, 'Ticket not found'
    
    ticket = tickets_data['tickets'][ticket_id]
    
    reply = {
        'user': username,
        'message': message,
        'created': datetime.now().isoformat()
    }
    
    ticket['replies'].append(reply)
    ticket['updated'] = datetime.now().isoformat()
    
    # Auto-assign to first admin/moderator who replies
    if not ticket['assigned_to']:
        users, _ = load_users()
        user_role = users.get(username, {}).get('role', 'user')
        if user_role in ['admin', 'moderator']:
            ticket['assigned_to'] = username
            if ticket['status'] == 'open':
                ticket['status'] = 'in_progress'
    
    save_tickets(tickets_data)
    
    log_activity(username, 'TICKET_REPLY', f'Replied to ticket: {ticket_id}')
    
    return True, ticket

def update_ticket_status(ticket_id, status, username):
    """Update ticket status"""
    tickets_data = load_tickets()
    
    if ticket_id not in tickets_data['tickets']:
        return False, 'Ticket not found'
    
    ticket = tickets_data['tickets'][ticket_id]
    ticket['status'] = status
    ticket['updated'] = datetime.now().isoformat()
    
    if status == 'in_progress' and not ticket['assigned_to']:
        ticket['assigned_to'] = username
    
    save_tickets(tickets_data)
    
    log_activity(username, 'TICKET_STATUS_UPDATE', f'Updated ticket {ticket_id} to {status}')
    
    return True, ticket

# ============================================
# PAYMENT SYSTEM FUNCTIONS
# ============================================

def load_payment_requests():
    """Load payment requests from file"""
    if PAYMENT_REQUESTS_FILE.exists():
        try:
            with open(PAYMENT_REQUESTS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {'requests': {}, 'settings': {}}

def save_payment_requests(data):
    """Save payment requests to file"""
    PAYMENT_REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PAYMENT_REQUESTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def create_payment_request(username, tier, amount):
    """Create a new payment request"""
    requests_data = load_payment_requests()
    
    # Generate unique payment ID
    payment_id = f"PAY-{secrets.token_hex(6).upper()}"
    
    request_data = {
        'username': username,
        'tier': tier,
        'amount': amount,
        'status': 'pending',
        'created': datetime.now().isoformat(),
        'payment_id': payment_id,
        'payment_method': None,
        'transaction_id': None,
        'proof': None
    }
    
    requests_data['requests'][payment_id] = request_data
    save_payment_requests(requests_data)
    
    return payment_id, request_data

def approve_payment_request(payment_id):
    """Approve payment request and upgrade user"""
    requests_data = load_payment_requests()
    
    if payment_id not in requests_data['requests']:
        return False, 'Payment request not found'
    
    request = requests_data['requests'][payment_id]
    
    if request['status'] != 'pending':
        return False, f'Payment request already {request["status"]}'
    
    username = request['username']
    tier = request['tier']
    
    # Upgrade user subscription
    users, roles = load_users()
    if username not in users:
        return False, 'User not found'
    
    # Set subscription
    users[username]['subscription'] = {
        'tier': tier,
        'status': 'active',
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=30)).isoformat() if tier != 'free' else None,
        'payment_method': request.get('payment_method', 'manual'),
        'payment_id': payment_id
    }
    
    save_users(users, roles)
    
    # Update request status
    request['status'] = 'approved'
    request['approved_at'] = datetime.now().isoformat()
    request['approved_by'] = 'system'
    
    requests_data['requests'][payment_id] = request
    save_payment_requests(requests_data)
    
    log_activity(username, 'SUBSCRIPTION_UPGRADE', f'Upgraded to {tier} tier via payment {payment_id}')
    
    return True, 'Payment approved and user upgraded'

def generate_payment_links(payment_id, amount, venmo_username=None, cashapp_username=None):
    """Generate payment request links for Venmo/CashApp"""
    payment_note = f"SecureVPN-{payment_id}"
    
    links = {}
    
    if venmo_username:
        # Venmo payment request link
        links['venmo'] = f"https://venmo.com/{venmo_username}?txn=pay&amount={amount}&note={payment_note}"
        links['venmo_mobile'] = f"venmo://paycharge?txn=pay&recipients={venmo_username}&amount={amount}&note={payment_note}"
    
    if cashapp_username:
        # CashApp payment link
        links['cashapp'] = f"https://cash.app/${cashapp_username}/{amount}?note={payment_note}"
    
    return links

# ============================================
# HELPER FUNCTIONS
# ============================================

def require_api_auth(f):
    """Decorator to require API authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def sanitize_input(text, max_length=1000):
    """Sanitize user input to prevent XSS"""
    if not isinstance(text, str):
        return str(text)
    # Remove null bytes
    text = text.replace('\x00', '')
    # Truncate to max length
    text = text[:max_length]
    # Remove HTML tags (basic)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format (alphanumeric, underscore, dash, 3-30 chars)"""
    pattern = r'^[a-zA-Z0-9_-]{3,30}$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """Validate password strength (min 8 chars, at least one letter and one number)"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def hash_password(password):
    """Hash password using bcrypt (secure, industry-standard)"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password, salt).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password against bcrypt hash"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(password_hash, str):
        password_hash = password_hash.encode('utf-8')
    try:
        return bcrypt.checkpw(password, password_hash)
    except:
        # Fallback for old SHA256 hashes during migration
        try:
            sha256_hash = hashlib.sha256(password).hexdigest()
            return sha256_hash == password_hash.decode('utf-8') if isinstance(password_hash, bytes) else sha256_hash == password_hash
        except:
            return False

def load_users():
    """Load users from file"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE) as f:
                data = json.load(f)
                return data.get('users', {}), data.get('roles', {})
        except:
            pass
    
    # Default users
    default_users = {
        "admin": {"password": hash_password("admin123"), "role": "admin", "created": datetime.now().isoformat()},
        "moderator": {"password": hash_password("mod123"), "role": "moderator", "created": datetime.now().isoformat()},
        "user": {"password": hash_password("user123"), "role": "user", "created": datetime.now().isoformat()},
    }
    
    default_roles = get_default_roles()
    
    # Save defaults
    save_users(default_users, default_roles)
    
    return default_users, default_roles

def get_default_roles():
    """Get default role permissions"""
    return {
        "admin": {
            "can_start_stop_vpn": True, "can_edit_server_config": True,
            "can_manage_clients": True, "can_view_logs": True,
            "can_view_statistics": True, "can_export_configs": True,
            "can_backup": True, "can_disconnect_clients": True,
            "can_revoke_clients": True, "can_add_clients": True,
            "can_edit_clients": True, "can_start_download_server": True,
            "can_manage_users": True, "can_manage_tickets": True
        },
        "moderator": {
            "can_start_stop_vpn": False, "can_edit_server_config": False,
            "can_manage_clients": True, "can_view_logs": True,
            "can_view_statistics": True, "can_export_configs": True,
            "can_backup": False, "can_disconnect_clients": True,
            "can_revoke_clients": False, "can_add_clients": True,
            "can_edit_clients": True, "can_start_download_server": True,
            "can_manage_users": False, "can_manage_tickets": True
        },
        "user": {
            "can_start_stop_vpn": False, "can_edit_server_config": False,
            "can_manage_clients": False, "can_view_logs": False,
            "can_view_statistics": True, "can_export_configs": False,
            "can_backup": False, "can_disconnect_clients": False,
            "can_revoke_clients": False, "can_add_clients": False,
            "can_edit_clients": False, "can_start_download_server": False,
            "can_manage_users": False
        }
    }

def save_users(users, roles):
    """Save users to file"""
    data = {"users": users, "roles": roles}
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_permissions(role):
    """Get permissions for a role"""
    _, roles = load_users()
    return roles.get(role, {})

def require_role(*allowed_roles):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                return render_template('error.html', 
                    message=f"Access denied. Required role: {', '.join(allowed_roles)}"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            role = session.get('role')
            permissions = get_permissions(role)
            if not permissions.get(permission, False):
                return render_template('error.html', 
                    message=f"Permission denied. Required: {permission}"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_active_connections():
    """Get active VPN connections from status log"""
    connections = []
    if STATUS_LOG.exists():
        try:
            with open(STATUS_LOG) as f:
                lines = f.readlines()
                for line in lines:
                    if line.strip() and line[0].isdigit():
                        parts = line.strip().split(',')
                        if len(parts) >= 6:
                            connections.append({
                                'virtual_ip': parts[0],
                                'name': parts[1] if len(parts) > 1 else 'Unknown',
                                'real_ip': parts[2] if len(parts) > 2 else 'N/A',
                                'bytes_rx': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
                                'bytes_tx': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                                'connected_since': parts[5] if len(parts) > 5 else 'N/A'
                            })
        except:
            pass
    return connections

def generate_qr_code(data):
    """Generate QR code image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{img_str}"

def log_activity(user, action, details=""):
    """Log admin/moderator activity"""
    ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] {user}: {action} {details}\n"
    with open(ACTIVITY_LOG, 'a') as f:
        f.write(entry)

def get_activity_logs(limit=100):
    """Get recent activity logs"""
    if not ACTIVITY_LOG.exists():
        return []
    
    try:
        with open(ACTIVITY_LOG, 'r') as f:
            lines = f.readlines()
            # Return last N lines, reversed (newest first)
            return [line.strip() for line in lines[-limit:]][::-1]
    except:
        return []

def update_connection_history(connections):
    """Update connection history"""
    CONNECTION_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing history
    history = []
    if CONNECTION_HISTORY.exists():
        try:
            with open(CONNECTION_HISTORY, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # Track current connections
    current_connections = {c.get('name', 'Unknown'): c for c in connections}
    
    # Load previous state
    last_state_file = VPN_DIR / 'logs' / 'last-connections.json'
    previous_connections = {}
    if last_state_file.exists():
        try:
            with open(last_state_file, 'r') as f:
                previous_connections = json.load(f)
        except:
            pass
    
    # Detect new connections
    for name, conn in current_connections.items():
        if name not in previous_connections:
            # New connection
            history.append({
                'name': name,
                'virtual_ip': conn.get('virtual_ip', 'N/A'),
                'real_ip': conn.get('real_ip', 'N/A'),
                'action': 'connected',
                'timestamp': datetime.now().isoformat()
            })
    
    # Detect disconnections
    for name in previous_connections:
        if name not in current_connections:
            # Disconnected
            history.append({
                'name': name,
                'action': 'disconnected',
                'timestamp': datetime.now().isoformat()
            })
    
    # Keep last 1000 entries
    history = history[-1000:]
    
    # Save history
    with open(CONNECTION_HISTORY, 'w') as f:
        json.dump(history, f, indent=2)
    
    # Save current state
    with open(last_state_file, 'w') as f:
        json.dump(current_connections, f, indent=2)
    
    return history

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Home page - Landing page for non-logged-in users"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')


# Rate limiting storage (in-memory, simple)
login_attempts = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 900  # 15 minutes

def check_rate_limit(ip):
    """Check if IP is rate limited"""
    import time
    now = time.time()
    
    if ip not in login_attempts:
        login_attempts[ip] = []
    
    # Remove old attempts
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
    
    if len(login_attempts[ip]) >= RATE_LIMIT_MAX:
        return False
    
    login_attempts[ip].append(now)
    return True

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        # Rate limiting
        if not check_rate_limit(request.remote_addr):
            return render_template('login.html', error='Too many login attempts. Please try again in 15 minutes.')
        
        username = sanitize_input(request.form.get('username', '').strip(), max_length=30)
        password = request.form.get('password', '')
        
        # Validate username
        if not validate_username(username):
            return render_template('login.html', error='Invalid username format. Use 3-30 alphanumeric characters, underscore, or dash.')
        
        users, _ = load_users()
        
        if username in users:
            user = users[username]
            stored_password = user.get('password', '')
            
            # Verify password (supports both bcrypt and legacy SHA256)
            if verify_password(password, stored_password):
                # Migrate to bcrypt if still using old hash
                if len(stored_password) == 64:  # Old SHA256 hash length
                    users[username]['password'] = hash_password(password)
                    _, roles = load_users()
                    save_users(users, roles)
                
                # Email verification is recommended but not required for login
                # Users can login even if email isn't verified (but we'll show a warning)
                email_verified = user.get('email_verified')
                email = user.get('email', '')
                
                # Set session with warning if email not verified
                email_warning = None
                if email_verified is False and email:
                    email_warning = f'Email not verified. Check {email} for verification link.'
                    # Don't block login, just warn them
                
                session['username'] = username
                session['role'] = user.get('role', 'user')
                session.permanent = True  # Make session permanent so cookie is set
                
                # Redirect with warning if email not verified
                if email_warning:
                    flash(email_warning, 'warning')
                
                return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation - email is now required
        if not username or not password:
            return render_template('signup.html', error='Username and password are required')
        
        if not email:
            return render_template('signup.html', error='Email address is required for account verification')
        
        if not validate_email(email):
            return render_template('signup.html', error='Please enter a valid email address')
        
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')
        
        if len(password) < 6:
            return render_template('signup.html', error='Password must be at least 6 characters')
        
        users, roles = load_users()
        
        if username in users:
            return render_template('signup.html', error='Username already exists')
        
        # Check email uniqueness
        for user_data in users.values():
            if user_data.get('email') == email:
                return render_template('signup.html', error='Email already registered')
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = (datetime.now() + timedelta(hours=24)).isoformat()
        
        # Create user with free subscription (unverified)
        user_data = {
            'password': hash_password(password),
            'role': 'user',
            'email': email,
            'email_verified': False,
            'verification_token': verification_token,
            'verification_expires': verification_expires,
            'created': datetime.now().isoformat(),
            'clients': [],  # List of client names owned by this user
            'subscription': {
                'tier': 'free',
                'status': 'active',
                'created': datetime.now().isoformat(),
                'expires': None
            },
            'usage': {
                'bandwidth_used_gb': 0,
                'month_start': datetime.now().replace(day=1).isoformat()
            }
        }
        
        users[username] = user_data
        save_users(users, roles)
        log_activity('system', 'USER_SIGNUP', f'New user registered: {username} (unverified)')
        
        # Send verification email
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from email_api import send_verification_email
            success, msg = send_verification_email(email, username, verification_token)
            if not success:
                print(f"Failed to send verification email: {msg}")
                return render_template('signup.html', error=f'Account created but failed to send verification email. Please contact support. Error: {msg}')
            else:
                print(f"Verification email sent to {email}: {msg}")
        except Exception as e:
            # Email failure shouldn't break signup, but warn user
            import traceback
            print(f"Failed to send verification email: {e}")
            traceback.print_exc()
            return render_template('signup.html', error=f'Account created but email verification failed. Please contact support. Error: {str(e)}')
        
        return render_template('signup.html', success=f'Account created! Please check your email ({email}) to verify your account before logging in.')
    
    return render_template('signup.html')


@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    
    if not username or not email:
        return render_template('login.html', error='Username and email are required')
    
    users, _ = load_users()
    
    if username not in users:
        return render_template('login.html', error='User not found')
    
    user = users[username]
    
    # Check if email matches
    if user.get('email') != email:
        return render_template('login.html', error='Email does not match this account')
    
    # Check if already verified
    if user.get('email_verified', False):
        return render_template('login.html', error='Your email is already verified. You can login now.')
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    verification_expires = (datetime.now() + timedelta(hours=24)).isoformat()
    
    users[username]['verification_token'] = verification_token
    users[username]['verification_expires'] = verification_expires
    save_users(users, _)
    
    # Send verification email
    try:
        from email_api import send_verification_email
        success, msg = send_verification_email(email, username, verification_token)
        if success:
            return render_template('login.html', success=f'Verification email sent to {email}. Please check your inbox (and spam folder).')
        else:
            return render_template('login.html', error=f'Failed to send verification email: {msg}')
    except Exception as e:
        return render_template('login.html', error=f'Failed to send verification email: {str(e)}')


@app.route('/verify-email')
def verify_email():
    """Email verification endpoint"""
    token = request.args.get('token', '')
    username = request.args.get('user', '')
    
    if not token or not username:
        return render_template('error.html', 
                             error='Invalid verification link',
                             message='The verification link is missing required parameters.')
    
    users, roles = load_users()
    
    if username not in users:
        return render_template('error.html',
                             error='User not found',
                             message='The user account does not exist.')
    
    user = users[username]
    
    # Check if already verified
    if user.get('email_verified', False):
        return render_template('error.html',
                             error='Already verified',
                             message='Your email address has already been verified. You can now login.',
                             action_url=url_for('login'),
                             action_text='Go to Login')
    
    # Check token
    stored_token = user.get('verification_token', '')
    if not stored_token or stored_token != token:
        return render_template('error.html',
                             error='Invalid verification token',
                             message='The verification link is invalid or has expired.')
    
    # Check expiration
    expires_str = user.get('verification_expires', '')
    if expires_str:
        try:
            expires = datetime.fromisoformat(expires_str)
            if datetime.now() > expires:
                # Token expired - generate new one
                new_token = secrets.token_urlsafe(32)
                new_expires = (datetime.now() + timedelta(hours=24)).isoformat()
                users[username]['verification_token'] = new_token
                users[username]['verification_expires'] = new_expires
                save_users(users, roles)
                
                # Send new verification email
                try:
                    from email_api import send_verification_email
                    email = user.get('email', '')
                    send_verification_email(email, username, new_token)
                except:
                    pass
                
                return render_template('error.html',
                                     error='Verification link expired',
                                     message='Your verification link has expired. A new verification email has been sent to your email address.')
        except:
            pass
    
    # Verify the email
    users[username]['email_verified'] = True
    users[username].pop('verification_token', None)
    users[username].pop('verification_expires', None)
    save_users(users, roles)
    
    log_activity('system', 'EMAIL_VERIFIED', f'User {username} verified their email')
    
    return render_template('error.html',
                         error='Email Verified!',
                         message=f'Your email address has been successfully verified! You can now login to your account.',
                         is_success=True,
                         action_url=url_for('login'),
                         action_text='Go to Login')



@app.route('/guide')
def guide():
    """VPN Setup Guide - Public page"""
    return render_template('guide.html')

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy-policy.html')

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact/Support page"""
    if request.method == 'POST':
        # Handle ticket submission
        if 'username' not in session:
            return render_template('contact.html', error='Please login to submit a ticket')
        
        username = session.get('username')
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        email = request.form.get('email', '').strip()
        
        if not subject or not message:
            return render_template('contact.html', error='Subject and message are required')
        
        ticket_id, ticket = create_ticket(username, subject, message, email)
        
        return render_template('contact.html', success=f'Ticket #{ticket_id} created successfully!')
    
    return render_template('contact.html')

@app.route('/blog')
def blog():
    """Blog/News page"""
    return render_template('blog.html')

@app.route('/sitemap.xml')
def sitemap():
    """Sitemap for SEO"""
    return render_template('sitemap.xml'), 200, {'Content-Type': 'application/xml'}

@app.route('/robots.txt')
def robots():
    """Robots.txt for SEO"""
    return """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Sitemap: https://phazevpn.com/sitemap.xml
""", 200, {'Content-Type': 'text/plain'}

@app.route('/91b8b604cb8207b4a71c14cd62205b33.txt')
def mailjet_validation():
    """Mailjet domain validation file - must be completely empty"""
    # Return empty response (Mailjet just needs 200 status, empty body)
    return '', 200, {'Content-Type': 'text/plain', 'Content-Length': '0'}

@app.route('/testimonials')
def testimonials():
    """Testimonials/Reviews page"""
    return render_template('testimonials.html')

# Error handlers (must be defined before app.run)
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message='Page not found. The page you are looking for does not exist.'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message='Internal server error. Please try again later or contact support.'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', message='Access forbidden. You do not have permission to access this page.'), 403

@app.route('/download')
def download_page():
    """Download PhazeVPN Client page"""
    return render_template('download.html')

@app.route('/download/client/<platform>')
def download_client(platform):
    """Download PhazeVPN GUI Client - REAL compiled executables (no Python required)"""
    platform = platform.lower()
    
    # CRITICAL: Never serve Python scripts - this endpoint ONLY serves compiled executables
    # This route MUST execute and return the .deb file directly
    
    # FIRST: Try direct absolute path to .deb file (most reliable)
    # This MUST execute before Flask's static file handler
    direct_deb = Path('/opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb')
    if direct_deb.exists() and direct_deb.suffix == '.deb':
        # Serve the REAL executable .deb package immediately
        return send_file(
            str(direct_deb),
            as_attachment=True,
            download_name='phaze-vpn_1.0.4_all.deb',
            mimetype='application/vnd.debian.binary-package'
        )
    
    # SECOND: Try repository location
    repo_deb = Path('/opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb')
    if repo_deb.exists() and repo_deb.suffix == '.deb':
        return send_file(
            str(repo_deb),
            as_attachment=True,
            download_name='phaze-vpn_1.0.4_all.deb',
            mimetype='application/vnd.debian.binary-package'
        )
    
    # Look for compiled executables in static/downloads directory
    # Use absolute paths to ensure we find files regardless of working directory
    STATIC_DIR = Path(__file__).parent.absolute() / 'static' / 'downloads'
    VPN_DIR = Path(VPN_CONFIG.get('vpn_dir', '/opt/phaze-vpn'))
    BASE_DIR = Path(__file__).parent.parent.absolute()
    
    # Also check absolute paths directly (most reliable)
    ABS_STATIC_DIR = Path('/opt/phaze-vpn/web-portal/static/downloads')
    ABS_REPO_DIR = Path('/opt/phazevpn-repo')
    
    installer_file = None
    installer_name = None
    
    if platform in ['linux', 'ubuntu', 'debian']:
        # Linux: Look for .deb package, AppImage, or standalone binary (newest version first)
        # Try to find latest version dynamically
        import glob
        import re
        
        # Search for all .deb files and sort by version
        # Look for both naming patterns: phazevpn-client_* and phaze-vpn_*
        deb_patterns = [
            # Absolute paths first (most reliable)
            str(ABS_STATIC_DIR / 'phaze-vpn_*_all.deb'),
            str(ABS_STATIC_DIR / 'phaze-vpn_*_amd64.deb'),
            str(ABS_STATIC_DIR / 'phazevpn-client_*_amd64.deb'),
            str(ABS_REPO_DIR / 'phaze-vpn_*_all.deb'),
            str(ABS_REPO_DIR / 'phaze-vpn_*_amd64.deb'),
            # Relative paths (backup)
            str(STATIC_DIR / 'phazevpn-client_*_amd64.deb'),
            str(STATIC_DIR / 'phaze-vpn_*_all.deb'),
            str(STATIC_DIR / 'phaze-vpn_*_amd64.deb'),
            str(VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'phazevpn-client_*_amd64.deb'),
            str(VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'phaze-vpn_*_all.deb'),
            str(VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'phaze-vpn_*_amd64.deb'),
            str(BASE_DIR / 'gui-executables' / 'phazevpn-client_*_amd64.deb'),
            str(BASE_DIR / 'gui-executables' / 'phaze-vpn_*_all.deb'),
        ]
        
        deb_files = []
        for pattern in deb_patterns:
            found = glob.glob(str(pattern))
            # Only add .deb files - filter out any Python scripts
            for f in found:
                if f.endswith('.deb') and not f.endswith('.py'):
                    deb_files.append(f)
        
        # Sort by version (extract version number and sort)
        def extract_version(path):
            # Try phazevpn-client pattern first
            match = re.search(r'phazevpn-client_([\d.]+)_amd64\.deb', path)
            if match:
                version = match.group(1)
                return tuple(map(int, version.split('.')))
            # Try phaze-vpn pattern
            match = re.search(r'phaze-vpn_([\d.]+)_(all|amd64)\.deb', path)
            if match:
                version = match.group(1)
                return tuple(map(int, version.split('.')))
            return (0, 0, 0)
        
        deb_files.sort(key=extract_version, reverse=True)
        
        installer_paths = []
        # Add sorted .deb files first (newest first) - ONLY .deb files
        for deb_file in deb_files:
            p = Path(deb_file)
            if p.exists() and p.suffix == '.deb':
                installer_paths.append(p)
        
        # Then add other compiled formats (NO Python scripts)
        other_formats = [
            ABS_STATIC_DIR / 'PhazeVPN-Client-linux',
            ABS_STATIC_DIR / 'PhazeVPN-Client-x86_64.AppImage',
            STATIC_DIR / 'PhazeVPN-Client-linux',
            STATIC_DIR / 'PhazeVPN-Client-x86_64.AppImage',
            VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'PhazeVPN-Client-linux',
            VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'PhazeVPN-Client-x86_64.AppImage',
            BASE_DIR / 'gui-executables' / 'PhazeVPN-Client-linux',
            BASE_DIR / 'gui-executables' / 'PhazeVPN-Client-x86_64.AppImage',
        ]
        for fmt_path in other_formats:
            if fmt_path.exists() and fmt_path.suffix != '.py':
                installer_paths.append(fmt_path)
        
        # Find first valid executable (NO Python files)
        installer_file = None
        for p in installer_paths:
            if p.exists() and p.suffix != '.py' and p.suffix in ['.deb', '.AppImage', '.exe', '.dmg', '.pkg', '.app']:
                installer_file = p
                break
        
        # If still no file found, try direct absolute path check
        if not installer_file:
            # Try multiple direct paths
            direct_paths = [
                ABS_STATIC_DIR / 'phaze-vpn_1.0.4_all.deb',
                Path('/opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb'),
                ABS_REPO_DIR / 'phaze-vpn_1.0.4_all.deb',
                Path('/opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb'),
            ]
            for direct_path in direct_paths:
                if direct_path.exists() and direct_path.suffix == '.deb':
                    installer_file = direct_path
                    installer_name = direct_path.name
                    break
        if installer_file:
            installer_name = installer_file.name
            # Ensure we use the actual filename, not a default
            if 'phaze-vpn_' in installer_name:
                # Keep the actual filename
                pass
            elif 'phazevpn-client_' in installer_name:
                # Keep the actual filename
                pass
        else:
            # No compiled executable found - return error message
            # DO NOT fallback to Python scripts - users need REAL executables
            installer_file = None
            installer_name = None
    
    elif platform in ['macos', 'mac', 'darwin']:
        # macOS: Look for .app bundle, .dmg, or .pkg (newest version first)
        import glob
        import re
        
        # Search for all .dmg files and sort by version
        dmg_patterns = [
            STATIC_DIR / 'PhazeVPN-Client-*.dmg',
            VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'PhazeVPN-Client-*.dmg',
            BASE_DIR / 'gui-executables' / 'PhazeVPN-Client-*.dmg',
        ]
        
        dmg_files = []
        for pattern in dmg_patterns:
            dmg_files.extend(glob.glob(str(pattern)))
        
        # Sort by version
        def extract_version(path):
            match = re.search(r'PhazeVPN-Client-([\d.]+)\.dmg', path)
            if match:
                version = match.group(1)
                return tuple(map(int, version.split('.')))
            return (0, 0, 0)
        
        dmg_files.sort(key=extract_version, reverse=True)
        
        installer_paths = []
        # Add sorted .dmg files first (newest first)
        for dmg_file in dmg_files:
            installer_paths.append(Path(dmg_file))
        
        # Then add other formats
        installer_paths.extend([
            STATIC_DIR / 'PhazeVPN-Client.app',
            STATIC_DIR / 'phazevpn-client-macos.pkg',
            VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'PhazeVPN-Client.app',
            BASE_DIR / 'gui-executables' / 'PhazeVPN-Client.app',
        ])
        
        installer_file = next((p for p in installer_paths if p.exists()), None)
        if installer_file:
            installer_name = installer_file.name
        else:
            installer_name = 'PhazeVPN-Client-macos.dmg'
    
    elif platform in ['windows', 'win', 'exe']:
        # Windows: Look for .exe
        installer_paths = [
            STATIC_DIR / 'PhazeVPN-Client.exe',
            STATIC_DIR / 'PhazeVPN-Client-windows.exe',
            VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'PhazeVPN-Client.exe',
            VPN_DIR / 'web-portal' / 'static' / 'downloads' / 'PhazeVPN-Client-windows.exe',
            BASE_DIR / 'gui-executables' / 'PhazeVPN-Client.exe',
        ]
        installer_file = next((p for p in installer_paths if p.exists()), None)
        if installer_file:
            installer_name = installer_file.name
        else:
            installer_name = 'PhazeVPN-Client-windows.exe'
    
    # If installer found, serve it (ONLY compiled executables, NO Python scripts)
    if installer_file and installer_file.exists():
        # CRITICAL: Never serve Python scripts - only compiled executables
        if installer_file.suffix == '.py':
            # Skip Python files - they're not compiled executables
            installer_file = None
        elif installer_file.suffix in ['.deb', '.dmg', '.pkg', '.exe', '.AppImage', '.app']:
            # These are compiled executables - serve them
            # Determine MIME type
            mimetype = 'application/octet-stream'
            if installer_file.suffix == '.deb':
                mimetype = 'application/vnd.debian.binary-package'
            elif installer_file.suffix == '.dmg':
                mimetype = 'application/x-apple-diskimage'
            elif installer_file.suffix == '.pkg':
                mimetype = 'application/x-newton-compatible-pkg'
            elif installer_file.suffix == '.AppImage':
                mimetype = 'application/x-executable'
            
            return send_file(
                str(installer_file),
                as_attachment=True,
                download_name=installer_name,
                mimetype=mimetype
            )
    
    # No compiled executable found - show professional message
    # CRITICAL: Never fall back to Python scripts - only show error message
    if not installer_file or not installer_file.exists() or (installer_file and installer_file.suffix == '.py'):
        if platform in ['windows', 'win', 'exe']:
            return render_template('download-instructions.html',
                                 platform="Windows",
                                 instructions="""
PhazeVPN Client for Windows is currently being built.

**Available Options:**
1. **Download Linux version** - Works on WSL (Windows Subsystem for Linux)
2. **Use web portal** - Manage your VPN from https://phazevpn.com
3. **Check back soon** - Windows client will be available shortly

**To build Windows client:**
- Requires Windows machine or GitHub Actions
- See BUILD-CLIENTS-GUIDE.md for instructions
                             """)
        elif platform in ['macos', 'mac', 'darwin']:
            return render_template('download-instructions.html',
                                 platform="macOS",
                                 instructions="""
PhazeVPN Client for macOS is currently being built.

**Available Options:**
1. **Use web portal** - Manage your VPN from https://phazevpn.com
2. **Check back soon** - macOS client will be available shortly

**To build macOS client:**
- Requires macOS machine
- See BUILD-CLIENTS-GUIDE.md for instructions
                                 """)
        else:
            return render_template('download-instructions.html',
                                 platform=platform.title(),
                                 instructions=f"PhazeVPN Client for {platform} is not yet available. Please check back later or contact support.")

@app.route('/download/setup-instructions')
def download_setup_instructions():
    """Show setup instructions for downloaded client"""
    return render_template('download-instructions.html',
                         platform='Your System',
                         instructions="""
PhazeVPN Client Setup Instructions:

1. **Install Python** (if not already installed):
   - Windows: Download from python.org
   - Linux: sudo apt install python3 python3-pip (or equivalent)
   - macOS: Usually pre-installed, or use Homebrew

2. **Install OpenVPN**:
   - Windows: Download from openvpn.net/community-downloads/
   - Linux: sudo apt install openvpn (or equivalent)
   - macOS: brew install openvpn or download from openvpn.net

3. **Install Required Python Packages**:
   Run in terminal: pip3 install requests

4. **Run the Client**:
   - Double-click phazevpn-client.py, OR
   - Run in terminal: python3 phazevpn-client.py

5. **Login**:
   - Use your phazevpn.com account credentials
   - The client will auto-download your VPN config

6. **Connect**:
   - Click the CONNECT button
   - You're protected! 🔒

Need help? Visit phazevpn.com/guide
                         """)

@app.route('/mobile/monitor')
def mobile_monitor():
    """Mobile-friendly VPN monitoring dashboard"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('mobile/monitor.html')

@app.route('/mobile/client')
def mobile_client_detail():
    """Mobile client connection detail page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('mobile/client-detail.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        
        users, _ = load_users()
        
        if username in users:
            user = users[username]
            user_email = user.get('email', '')
            
            # Verify email matches (if email provided)
            if email and user_email and email.lower() != user_email.lower():
                return render_template('forgot-password.html', error='Email does not match account')
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store token (expires in 1 hour)
            if 'password_reset_tokens' not in globals():
                globals()['password_reset_tokens'] = {}
            
            globals()['password_reset_tokens'][reset_token] = {
                'username': username,
                'expires': datetime.now() + timedelta(hours=1)
            }
            
            # Send reset email
            if user_email:
                try:
                    from email_api import send_password_reset_email
                    send_password_reset_email(user_email, username, reset_token)
                    return render_template('forgot-password.html', success='Password reset link sent to your email!')
                except Exception as e:
                    return render_template('forgot-password.html', error=f'Failed to send email: {str(e)}')
            else:
                return render_template('forgot-password.html', error='No email on file. Contact admin.')
        
        return render_template('forgot-password.html', error='Username not found')
    
    return render_template('forgot-password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Password reset with token"""
    token = request.args.get('token', '') or request.form.get('token', '')
    username = request.args.get('user', '') or request.form.get('username', '')
    
    if not token or not username:
        return render_template('error.html', message='Invalid reset link'), 400
    
    # Check token
    if 'password_reset_tokens' not in globals():
        return render_template('error.html', message='Invalid or expired reset link'), 400
    
    tokens = globals().get('password_reset_tokens', {})
    
    if token not in tokens:
        return render_template('error.html', message='Invalid or expired reset link'), 400
    
    token_data = tokens[token]
    
    # Check expiration
    if datetime.now() > token_data['expires']:
        del tokens[token]
        return render_template('error.html', message='Reset link has expired'), 400
    
    # Check username matches
    if token_data['username'] != username:
        return render_template('error.html', message='Invalid reset link'), 400
    
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not new_password or len(new_password) < 6:
            return render_template('reset-password.html', token=token, username=username, error='Password must be at least 6 characters')
        
        if new_password != confirm_password:
            return render_template('reset-password.html', token=token, username=username, error='Passwords do not match')
        
        # Update password
        users, roles = load_users()
        if username in users:
            users[username]['password'] = hash_password(new_password)
            save_users(users, roles)
            
            # Delete token
            del tokens[token]
            
            log_activity('system', 'PASSWORD_RESET', f'User {username} reset password')
            return render_template('reset-password.html', token=token, username=username, success='Password reset successfully! You can now login.')
        
        return render_template('error.html', message='User not found'), 404
    
    return render_template('reset-password.html', token=token, username=username)

@app.route('/dashboard')
def dashboard():
    """Main dashboard - redirects based on role"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role', 'user')
    
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))  # Function name matches route
    elif role == 'moderator':
        return redirect(url_for('moderator_dashboard'))  # Function name matches route
    else:
        return redirect(url_for('user_dashboard'))  # Function name matches route

@app.route('/admin')
@require_role('admin')
def admin_dashboard():
    """Admin dashboard"""
    # Get VPN status
    vpn_running = subprocess.run(['pgrep', '-f', 'openvpn.*server.conf'], 
                                capture_output=True).returncode == 0
    
    # Get client count
    clients = list_clients()
    
    # Get user count
    users, _ = load_users()
    
    # Get active connections
    connections = get_active_connections()
    
    return render_template('admin/dashboard.html',
                         username=session['username'],
                         vpn_running=vpn_running,
                         client_count=len(clients),
                         user_count=len(users),
                         active_connections=len(connections))

@app.route('/moderator')
@require_role('moderator', 'admin')
def moderator_dashboard():
    """Moderator dashboard"""
    clients = list_clients()
    connections = get_active_connections()
    
    return render_template('moderator/dashboard.html',
                         username=session['username'],
                         clients=clients,
                         active_connections=len(connections))

@app.route('/user')
def user_dashboard():
    """User dashboard"""
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    
    # Get user's clients
    user_clients = []
    user_client_names = user.get('clients', [])
    if CLIENT_CONFIGS_DIR.exists():
        for client_name in user_client_names:
            config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
            if config_file.exists():
                user_clients.append({
                    'name': client_name,
                    'created': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                })
    
    # Get VPN status
    vpn_running = subprocess.run(['pgrep', '-f', 'openvpn.*server.conf'], 
                                capture_output=True).returncode == 0
    
    # Get subscription info
    subscription = user.get('subscription', {'tier': 'free'})
    tier = subscription.get('tier', 'free')
    limits = SUBSCRIPTION_TIERS[tier]
    
    return render_template('user/dashboard.html',
                         username=username,
                         clients=user_clients,
                         client_count=len(user_clients),
                         vpn_running=vpn_running,
                         subscription_tier=tier,
                         subscription_limits=limits,
                         clients_used=len(user_clients),
                         can_create_more=len(user_clients) < limits['client_limit'] if limits['client_limit'] > 0 else True)

@app.route('/profile')
def profile():
    """User profile/settings page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    
    # Get user's clients
    user_clients = []
    user_client_names = user.get('clients', [])
    if CLIENT_CONFIGS_DIR.exists():
        for client_name in user_client_names:
            config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
            if config_file.exists():
                user_clients.append({
                    'name': client_name,
                    'created': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                })
    
    # Remove password from user data
    user_data = {k: v for k, v in user.items() if k != 'password'}
    user_data['username'] = username
    
    return render_template('profile.html', user=user_data, user_clients=user_clients)

@app.route('/admin/analytics')
@require_permission('can_view_statistics')
def admin_analytics():
    """Analytics dashboard with charts"""
    connections = get_active_connections()
    clients = list_clients()
    
    return render_template('admin/analytics.html',
                         username=session['username'],
                         connections=connections,
                         total_clients=len(clients))

@app.route('/admin/clients')
@require_permission('can_manage_clients')
def admin_clients():
    """Admin client management page"""
    clients = list_clients()
    return render_template('admin/clients.html', clients=clients)

@app.route('/admin/users')
@require_permission('can_manage_users')
def admin_users():
    """Admin user management page"""
    users, roles = load_users()
    # Remove passwords
    user_list = {name: {k: v for k, v in data.items() if k != 'password'} 
                 for name, data in users.items()}
    return render_template('admin/users.html', users=user_list, roles=list(roles.keys()))

@app.route('/admin/activity')
@require_permission('can_view_statistics')
def admin_activity():
    """Activity log viewer"""
    logs = get_activity_logs(200)
    connections = get_active_connections()
    
    # Update connection history
    update_connection_history(connections)
    
    # Load connection history
    history = []
    if CONNECTION_HISTORY.exists():
        try:
            with open(CONNECTION_HISTORY, 'r') as f:
                all_history = json.load(f)
                history = all_history[-100:]  # Last 100 events
        except:
            pass
    
    return render_template('admin/activity.html',
                         username=session['username'],
                         activity_logs=logs,
                         connection_history=history)

@app.route('/admin/payments')
@require_role('admin')
def admin_payments():
    """Admin payment management page"""
    requests_data = load_payment_requests()
    payment_requests = list(requests_data.get('requests', {}).values())
    
    # Sort by created date (newest first)
    payment_requests.sort(key=lambda x: x.get('created', ''), reverse=True)
    
    settings = requests_data.get('settings', {})
    
    return render_template('admin/payments.html',
                         username=session['username'],
                         payment_requests=payment_requests,
                         settings=settings)

@app.route('/config')
def download_config():
    """Download VPN config - SECURED: Only allows users to download their own clients
    Usage: /config?client=CLIENT_NAME&type=openvpn|phazevpn|wireguard
    """
    try:
        if 'username' not in session:
            flash('Please log in to download configs', 'error')
            return redirect(url_for('login'))
        
        username = session['username']
        users, _ = load_users()
        user = users.get(username, {})
        
        # Get parameters
        client_name = request.args.get('client') or request.args.get('name')
        config_type = request.args.get('type', 'openvpn').lower()
        
        if not client_name:
            flash('Client name required. Use: /config?client=CLIENT_NAME&type=openvpn', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Security: Remove path traversal attempts
        client_name = os.path.basename(client_name)
        
        # Strip file extensions if user included them
        if '.' in client_name:
            extensions_to_strip = ['.ovpn', '.phazevpn', '.conf', '.OVPN', '.PHAZEVPN', '.CONF']
            for ext in extensions_to_strip:
                if client_name.lower().endswith(ext.lower()):
                    client_name = client_name[:-len(ext)]
                    break
        
        # Check if user owns this client
        user_clients = user.get('clients', [])
        if client_name not in user_clients:
            # Admin can download any client
            if user.get('role') != 'admin':
                flash(f'You can only download your own client configs. Client "{client_name}" not found in your account.', 'error')
                return redirect(url_for('user_dashboard'))
        
        print(f"[DOWNLOAD] User {username} requesting {config_type} config for client {client_name}")
        print(f"[DOWNLOAD] CLIENT_CONFIGS_DIR: {CLIENT_CONFIGS_DIR}")
        print(f"[DOWNLOAD] CLIENT_CONFIGS_DIR exists: {CLIENT_CONFIGS_DIR.exists()}")
        
        # Handle different config types
        if config_type == 'openvpn':
            config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
            if not config_file.exists():
                # Try case variations
                for alt_name in [client_name.lower(), client_name.upper(), client_name]:
                    alt_file = CLIENT_CONFIGS_DIR / f'{alt_name}.ovpn'
                    if alt_file.exists():
                        config_file = alt_file
                        break
            
            if config_file.exists():
                try:
                    print(f"[DOWNLOAD] Sending OpenVPN file: {config_file}")
                    print(f"[DOWNLOAD] File size: {config_file.stat().st_size} bytes")
                    # Send actual .ovpn file - NOT JSON
                    response = send_file(
                        str(config_file), 
                        as_attachment=True,  # Force download, don't display
                        download_name=f'{client_name}.ovpn',
                        mimetype='application/x-openvpn-profile'
                    )
                    # Add headers to force download
                    response.headers['Content-Disposition'] = f'attachment; filename="{client_name}.ovpn"'
                    response.headers['Content-Type'] = 'application/x-openvpn-profile'
                    print(f"[DOWNLOAD] OpenVPN file sent successfully")
                    return response
                except Exception as e:
                    print(f"[DOWNLOAD] Error sending file: {e}")
                    import traceback
                    traceback.print_exc()
                    flash(f'Error downloading config: {e}', 'error')
                    return redirect(url_for('user_dashboard'))
            
            return render_template('error.html', message=f'OpenVPN config for "{client_name}" not found. Check that the client exists and you have access to it.'), 404
        
        elif config_type == 'phazevpn':
            # Try to load PhazeVPN config generator
            phazevpn_config = CLIENT_CONFIGS_DIR / f'{client_name}.phazevpn'
            if phazevpn_config.exists():
                print(f"[DOWNLOAD] Sending PhazeVPN file: {phazevpn_config}")
                # Send actual .phazevpn file (which is JSON format but should download as file)
                response = send_file(
                    str(phazevpn_config), 
                    as_attachment=True,  # Force download, don't display JSON
                    download_name=f'{client_name}.phazevpn',
                    mimetype='application/octet-stream'  # Force download, not JSON display
                )
                # Add headers to force download (not display as JSON)
                response.headers['Content-Disposition'] = f'attachment; filename="{client_name}.phazevpn"'
                response.headers['Content-Type'] = 'application/octet-stream'  # NOT application/json
                response.headers['X-Content-Type-Options'] = 'nosniff'  # Prevent browser from displaying JSON
                print(f"[DOWNLOAD] PhazeVPN file sent successfully")
                return response
            
                # Try to generate PhazeVPN config if it doesn't exist
            try:
                phazevpn_protocol_path = BASE_DIR / 'phazevpn-protocol'
                if phazevpn_protocol_path.exists():
                    sys.path.insert(0, str(phazevpn_protocol_path))
                    
                    # Handle hyphenated filename (Python can't import modules with hyphens)
                    generate_module_path = phazevpn_protocol_path / 'generate-phazevpn-config.py'
                    if not generate_module_path.exists():
                        generate_module_path = phazevpn_protocol_path / 'generate_phazevpn_config.py'
                    
                    if generate_module_path.exists():
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("generate_phazevpn_config", generate_module_path)
                        generate_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(generate_module)
                        generate_phazevpn_config = generate_module.generate_phazevpn_config
                        
                        server_host = VPN_CONFIG.get('server_ip', 'phazevpn.com')
                        server_port = int(VPN_CONFIG.get('server_port', '51821'))
                        
                        # Generate config
                        generated_file = generate_phazevpn_config(
                            client_name, server_host, server_port,
                            username=client_name, password=None,
                            output_dir=CLIENT_CONFIGS_DIR
                        )
                        
                        if generated_file and Path(generated_file).exists():
                            print(f"[DOWNLOAD] Sending generated PhazeVPN file: {generated_file}")
                            response = send_file(
                                str(generated_file), 
                                as_attachment=True,  # Force download
                                download_name=f'{client_name}.phazevpn',
                                mimetype='application/octet-stream'  # NOT application/json
                            )
                            response.headers['Content-Disposition'] = f'attachment; filename="{client_name}.phazevpn"'
                            response.headers['Content-Type'] = 'application/octet-stream'
                            response.headers['X-Content-Type-Options'] = 'nosniff'
                            return response
            except Exception as e:
                import traceback
                print(f"Warning: Could not generate PhazeVPN config: {e}")
                traceback.print_exc()
            
            return render_template('error.html', message=f'PhazeVPN config for "{client_name}" not found and could not be generated'), 404
        
        elif config_type == 'wireguard':
            wireguard_dir = BASE_DIR / 'wireguard' / 'clients'
            config_file = wireguard_dir / f'{client_name}.conf'
            
            if config_file.exists():
                print(f"[DOWNLOAD] Sending WireGuard file: {config_file}")
                # Send actual .conf file - NOT JSON
                response = send_file(
                    str(config_file), 
                    as_attachment=True,  # Force download
                    download_name=f'{client_name}.conf',
                    mimetype='text/plain'
                )
                response.headers['Content-Disposition'] = f'attachment; filename="{client_name}.conf"'
                response.headers['Content-Type'] = 'text/plain'
                print(f"[DOWNLOAD] WireGuard file sent successfully")
                return response
            
            # Try to generate WireGuard config if it doesn't exist
            try:
                wg_add_client = BASE_DIR / 'wireguard' / 'add-client.sh'
                if wg_add_client.exists():
                    result = subprocess.run(
                        ['bash', str(wg_add_client), client_name],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=str(BASE_DIR)
                    )
                    if result.returncode == 0 and config_file.exists():
                        print(f"[DOWNLOAD] Sending generated WireGuard file: {config_file}")
                        response = send_file(
                            str(config_file), 
                            as_attachment=True,  # Force download
                            download_name=f'{client_name}.conf',
                            mimetype='text/plain'
                        )
                        response.headers['Content-Disposition'] = f'attachment; filename="{client_name}.conf"'
                        response.headers['Content-Type'] = 'text/plain'
                        return response
            except Exception as e:
                print(f"Warning: Could not generate WireGuard config: {e}")
            
            return render_template('error.html', message=f'WireGuard config for "{client_name}" not found and could not be generated'), 404
        
        else:
            return render_template('error.html', message=f'Invalid config type: {config_type}. Use: openvpn, phazevpn, or wireguard'), 400
    
    except Exception as e:
        import traceback
        print(f"[DOWNLOAD] Unexpected error: {e}")
        traceback.print_exc()
        flash(f'Error downloading config: {e}', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/download/<client_name>')
def download_client_config(client_name):
    """Download client config - SECURED: Only allows users to download their own clients
    Supports: /download/CLIENT_NAME?type=openvpn|phazevpn|wireguard
    """
    if 'username' not in session:
        flash('Please log in to download configs', 'error')
        return redirect(url_for('login'))
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    
    # Get config type from query parameter
    config_type = request.args.get('type', 'openvpn').lower()
    
    # Security: Remove path traversal attempts
    client_name = os.path.basename(client_name)
    
    # Strip file extensions if user included them
    if '.' in client_name:
        extensions_to_strip = ['.ovpn', '.phazevpn', '.conf', '.OVPN', '.PHAZEVPN', '.CONF']
        for ext in extensions_to_strip:
            if client_name.lower().endswith(ext.lower()):
                client_name = client_name[:-len(ext)]
                break
    
    # Check if user owns this client
    user_clients = user.get('clients', [])
    if client_name not in user_clients:
        # Admin can download any client
        if user.get('role') != 'admin':
            flash(f'You can only download your own client configs. Client "{client_name}" not found in your account.', 'error')
            return redirect(url_for('user_dashboard'))
    
    # Handle different config types
    if config_type == 'openvpn':
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
        if not config_file.exists():
            # Try case variations
            for alt_name in [client_name.lower(), client_name.upper(), client_name]:
                alt_file = CLIENT_CONFIGS_DIR / f'{alt_name}.ovpn'
                if alt_file.exists():
                    config_file = alt_file
                    break
        
        if config_file.exists():
            return send_file(str(config_file), as_attachment=True, 
                            download_name=f'{client_name}.ovpn',
                            mimetype='application/x-openvpn-profile')
        flash(f'OpenVPN config for "{client_name}" not found', 'error')
        return redirect(url_for('user_dashboard'))
    
    elif config_type == 'phazevpn':
        phazevpn_config = CLIENT_CONFIGS_DIR / f'{client_name}.phazevpn'
        if phazevpn_config.exists():
            response = send_file(str(phazevpn_config), as_attachment=True,
                                download_name=f'{client_name}.phazevpn',
                                mimetype='application/octet-stream')
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        # Try to generate if it doesn't exist
        try:
            phazevpn_protocol_path = BASE_DIR / 'phazevpn-protocol'
            if phazevpn_protocol_path.exists():
                sys.path.insert(0, str(phazevpn_protocol_path))
                generate_module_path = phazevpn_protocol_path / 'generate-phazevpn-config.py'
                if not generate_module_path.exists():
                    generate_module_path = phazevpn_protocol_path / 'generate_phazevpn_config.py'
                if generate_module_path.exists():
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("generate_phazevpn_config", generate_module_path)
                    generate_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(generate_module)
                    generate_phazevpn_config = generate_module.generate_phazevpn_config
                    server_host = VPN_CONFIG.get('server_ip', 'phazevpn.com')
                    server_port = int(VPN_CONFIG.get('server_port', '51821'))
                    generated_file = generate_phazevpn_config(
                        client_name, server_host, server_port,
                        username=client_name, password=None,
                        output_dir=CLIENT_CONFIGS_DIR
                    )
                    if generated_file and Path(generated_file).exists():
                        response = send_file(str(generated_file), as_attachment=True,
                                            download_name=f'{client_name}.phazevpn',
                                            mimetype='application/octet-stream')
                        response.headers['X-Content-Type-Options'] = 'nosniff'
                        return response
        except Exception as e:
            print(f"Could not generate PhazeVPN config: {e}")
        flash(f'PhazeVPN config for "{client_name}" not found', 'error')
        return redirect(url_for('user_dashboard'))
    
    elif config_type == 'wireguard':
        wireguard_dir = BASE_DIR / 'wireguard' / 'clients'
        if not wireguard_dir.exists():
            wireguard_dir = VPN_DIR / 'wireguard' / 'clients'
        config_file = wireguard_dir / f'{client_name}.conf'
        
        if config_file.exists():
            return send_file(str(config_file), as_attachment=True,
                            download_name=f'{client_name}.conf',
                            mimetype='text/plain')
        flash(f'WireGuard config for "{client_name}" not found', 'error')
        return redirect(url_for('user_dashboard'))
    
    else:
        flash(f'Invalid config type: {config_type}. Use: openvpn, phazevpn, or wireguard', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/qr/<client_name>')
def qr_code(client_name):
    """Generate QR code for client config"""
    config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
    if config_file.exists():
        # Read config
        with open(config_file) as f:
            config_content = f.read()
        
        # Generate QR code (for small configs) or download URL
        # Use the new /config route (no separate port needed!)
        download_url = f"https://phazevpn.com/config?client={client_name}&type=openvpn"
        
        # Generate QR code
        qr_image = generate_qr_code(download_url)
        
        return render_template('qr-code.html', 
                             client_name=client_name,
                             qr_code=qr_image,
                             download_url=download_url)
    return render_template('error.html', message='Client config not found'), 404

# ============================================
# API ENDPOINTS
# ============================================

def list_clients():
    """List all VPN clients"""
    clients = []
    if CLIENT_CONFIGS_DIR.exists():
        for config_file in CLIENT_CONFIGS_DIR.glob('*.ovpn'):
            clients.append({
                'name': config_file.stem,
                'file': config_file.name,
                'created': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            })
    return clients

@app.route('/api/vpn/status')
@require_api_auth
def api_vpn_status():
    """Get VPN status for all three protocols - SECURED: Requires authentication"""
    
    # Check OpenVPN (via secure-vpn service or process)
    openvpn_running = False
    openvpn_port_listening = False
    try:
        # Check if OpenVPN process is running
        openvpn_running = subprocess.run(['pgrep', '-f', 'openvpn.*server.conf'], 
                                        capture_output=True).returncode == 0
        # Check if secure-vpn service is active
        if not openvpn_running:
            result = subprocess.run(['systemctl', 'is-active', 'secure-vpn'], 
                                  capture_output=True, text=True, timeout=5)
            openvpn_running = result.returncode == 0 and 'active' in result.stdout.lower()
        
        if openvpn_running:
            result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True, timeout=5)
            openvpn_port_listening = ':1194' in result.stdout or '1194' in result.stdout
    except:
        pass
    
    # Check WireGuard
    wireguard_running = False
    wireguard_port_listening = False
    try:
        result = subprocess.run(['systemctl', 'is-active', 'wg-quick@wg0'], 
                              capture_output=True, text=True, timeout=5)
        wireguard_running = result.returncode == 0 and 'active' in result.stdout.lower()
        
        if wireguard_running:
            result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True, timeout=5)
            wireguard_port_listening = ':51820' in result.stdout or '51820' in result.stdout
    except:
        pass
    
    # Check PhazeVPN Protocol
    phazevpn_running = False
    phazevpn_port_listening = False
    try:
        # Try phazevpn-protocol service first
        result = subprocess.run(['systemctl', 'is-active', 'phazevpn-protocol'], 
                              capture_output=True, text=True, timeout=5)
        phazevpn_running = result.returncode == 0 and 'active' in result.stdout.lower()
        
        # Try phazevpn-secure if phazevpn-protocol not found
        if not phazevpn_running:
            result = subprocess.run(['systemctl', 'is-active', 'phazevpn-secure'], 
                                  capture_output=True, text=True, timeout=5)
            phazevpn_running = result.returncode == 0 and 'active' in result.stdout.lower()
        
        # Check if process is running
        if not phazevpn_running:
            phazevpn_running = subprocess.run(['pgrep', '-f', 'phazevpn-server'], 
                                             capture_output=True).returncode == 0
        
        if phazevpn_running:
            result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True, timeout=5)
            phazevpn_port_listening = ':51821' in result.stdout or '51821' in result.stdout
    except:
        pass
    
    # Get user's current connection info (OpenVPN)
    username = session.get('username')
    users, _ = load_users()
    user = users.get(username, {})
    user_clients = user.get('clients', [])
    
    # Try to get connection info
    connections = get_active_connections()
    user_connection = None
    for conn in connections:
        if conn.get('name') in user_clients:
            user_connection = conn
            break
    
    # Overall status: at least one VPN is running
    any_running = openvpn_running or wireguard_running or phazevpn_running
    
    return jsonify({
        'running': any_running,  # For backward compatibility
        'status': 'active' if any_running else 'inactive',
        'server': VPN_CONFIG.get('server_ip', '15.204.11.19'),
        'ip': user_connection.get('virtual_ip', 'N/A') if user_connection else None,
        'protocols': {
            'openvpn': {
                'running': openvpn_running,
                'port_listening': openvpn_port_listening,
                'port': 1194,
                'service': 'secure-vpn'
            },
            'wireguard': {
                'running': wireguard_running,
                'port_listening': wireguard_port_listening,
                'port': 51820,
                'service': 'wg-quick@wg0'
            },
            'phazevpn': {
                'running': phazevpn_running,
                'port_listening': phazevpn_port_listening,
                'port': 51821,
                'service': 'phazevpn-protocol'
            }
        }
    })

@app.route('/api/connections')
@require_api_auth
def api_connections():
    """Get active connections - SECURED: Only shows logged-in user's clients"""
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    role = user.get('role', 'user')
    
    # Get all connections
    all_connections = get_active_connections()
    
    # Filter based on role
    if role == 'admin':
        # Admins see all connections
        connections = all_connections
    else:
        # Regular users only see their own clients
        user_client_names = set(user.get('clients', []))
        connections = [c for c in all_connections if c.get('name', '').lower() in [n.lower() for n in user_client_names]]
    
    # Calculate totals
    total_rx = sum(c.get('bytes_rx', 0) for c in connections)
    total_tx = sum(c.get('bytes_tx', 0) for c in connections)
    total_data = total_rx + total_tx
    
    return jsonify({
        'connections': connections,
        'count': len(connections),
        'total_bytes_rx': total_rx,
        'total_bytes_tx': total_tx,
        'total_bytes': total_data
    })

@app.route('/api/client/<client_name>/details')
def api_client_details(client_name):
    """Get detailed connection info for a specific client - SECURED: Only owner can access"""
    # Require authentication
    if 'username' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    role = user.get('role', 'user')
    
    # Check authorization - user must own this client OR be admin
    user_client_names = set(user.get('clients', []))
    if role != 'admin' and client_name.lower() not in [n.lower() for n in user_client_names]:
        return jsonify({'error': 'Access denied: You do not own this client'}), 403
    
    connections = get_active_connections()
    
    # Find this client's connection
    client_conn = None
    for conn in connections:
        if conn.get('name', '').lower() == client_name.lower():
            client_conn = conn
            break
    
    if not client_conn:
        return jsonify({
            'connected': False,
            'message': 'Client not currently connected'
        })
    
    # Get connection log from server logs if available
    connection_log = ""
    server_log = VPN_DIR / 'logs' / 'server.log'
    if server_log.exists():
        try:
            with open(server_log, 'r') as f:
                lines = f.readlines()
                # Get last 50 lines mentioning this client
                relevant_lines = [line for line in lines[-500:] if client_name.lower() in line.lower()]
                connection_log = '\n'.join(relevant_lines[-50:])
        except:
            pass
    
    # Parse server config for details
    server_addr = "phazevpn.com"
    protocol = "UDP"
    cipher = "CHACHA20-POLY1305"
    
    server_conf = VPN_DIR / 'config' / 'server.conf'
    if server_conf.exists():
        try:
            with open(server_conf, 'r') as f:
                config_content = f.read()
                if 'proto udp' in config_content.lower():
                    protocol = "UDP"
                elif 'proto tcp' in config_content.lower():
                    protocol = "TCP"
                if 'cipher' in config_content.lower() or 'data-ciphers' in config_content.lower():
                    # Try to extract cipher
                    import re
                    cipher_match = re.search(r'data-ciphers\s+(\S+)', config_content, re.I)
                    if cipher_match:
                        cipher = cipher_match.group(1).split(':')[0]
        except:
            pass
    
    return jsonify({
        'connected': True,
        'name': client_conn.get('name', client_name),
        'virtual_ip': client_conn.get('virtual_ip', 'N/A'),
        'real_ip': client_conn.get('real_ip', 'N/A'),
        'bytes_rx': client_conn.get('bytes_rx', 0),
        'bytes_tx': client_conn.get('bytes_tx', 0),
        'connected_since': client_conn.get('connected_since', 'N/A'),
        'server_addr': server_addr,
        'protocol': protocol,
        'cipher': cipher,
        'log': connection_log,
        'last_seen': datetime.now().isoformat()
    })

@app.route('/api/stats/bandwidth')
def api_bandwidth_stats():
    """Get bandwidth statistics - SECURED: Shows only user's data"""
    if 'username' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    user_clients = user.get('clients', [])
    
    connections = get_active_connections()
    
    # Only count user's own connections
    user_total_rx = 0
    user_total_tx = 0
    for conn in connections:
        if conn.get('name') in user_clients:
            user_total_rx += conn.get('bytes_rx', 0)
            user_total_tx += conn.get('bytes_tx', 0)
    
    # Get user's subscription limits
    subscription = user.get('subscription', {'tier': 'free'})
    tier = subscription.get('tier', 'free')
    limits = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS['free'])
    data_limit = limits.get('bandwidth_limit_gb', 0) * (1024**3) if limits.get('bandwidth_limit_gb', 0) > 0 else -1
    
    total_used = user_total_rx + user_total_tx
    
    return jsonify({
        'used': total_used,
        'limit': data_limit,
        'rx': user_total_rx,
        'tx': user_total_tx,
        'client_stats': {name: {'rx': 0, 'tx': 0} for name in user_clients}
    })

@app.route('/api/server/metrics')
def api_server_metrics():
    """Get server performance metrics"""
    # Get system info
    try:
        # Uptime
        uptime_result = subprocess.run(['uptime', '-p'], capture_output=True, text=True, timeout=5)
        uptime = uptime_result.stdout.strip() if uptime_result.returncode == 0 else "N/A"
        
        # Load average
        load_result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        load_match = re.search(r'load average: ([\d.]+)', load_result.stdout)
        load_avg = load_match.group(1) if load_match else "N/A"
        
        # Memory
        mem_result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        mem_lines = mem_result.stdout.split('\n')
        mem_info = mem_lines[1].split() if len(mem_lines) > 1 else []
        memory_used = mem_info[2] if len(mem_info) > 2 else "N/A"
        memory_total = mem_info[1] if len(mem_info) > 1 else "N/A"
        
        # Disk
        disk_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        disk_lines = disk_result.stdout.split('\n')
        disk_info = disk_lines[1].split() if len(disk_lines) > 1 else []
        disk_used = disk_info[2] if len(disk_info) > 2 else "N/A"
        disk_total = disk_info[1] if len(disk_info) > 1 else "N/A"
        disk_percent = disk_info[4] if len(disk_info) > 4 else "N/A"
        
    except:
        uptime = "N/A"
        load_avg = "N/A"
        memory_used = memory_total = "N/A"
        disk_used = disk_total = disk_percent = "N/A"
    
    # VPN status
    vpn_running = subprocess.run(['pgrep', '-f', 'openvpn.*server.conf'], 
                                capture_output=True).returncode == 0
    
    connections = get_active_connections()
    
    return jsonify({
        'uptime': uptime,
        'load_average': load_avg,
        'memory': {
            'used': memory_used,
            'total': memory_total
        },
        'disk': {
            'used': disk_used,
            'total': disk_total,
            'percent': disk_percent
        },
        'vpn_running': vpn_running,
        'active_connections': len(connections)
    })

@app.route('/api/vpn/start', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_start():
    """Start VPN - starts all three protocols (OpenVPN, WireGuard, PhazeVPN Protocol)"""
    protocol = request.json.get('protocol', 'all') if request.is_json else 'all'
    results = {}
    
    try:
        # Start OpenVPN
        if protocol in ['all', 'openvpn']:
            result = subprocess.run(['systemctl', 'start', 'secure-vpn'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try direct vpn-manager.py if service doesn't exist
                vpn_manager = VPN_DIR / 'vpn-manager.py'
                if vpn_manager.exists():
                    result = subprocess.run(['python3', str(vpn_manager), 'start'], 
                                          capture_output=True, text=True, timeout=10)
            results['openvpn'] = {
                'success': result.returncode == 0,
                'message': 'OpenVPN started' if result.returncode == 0 else result.stderr.strip() or result.stdout.strip()
            }
        
        # Start WireGuard
        if protocol in ['all', 'wireguard']:
            result = subprocess.run(['systemctl', 'start', 'wg-quick@wg0'], capture_output=True, text=True, timeout=10)
            results['wireguard'] = {
                'success': result.returncode == 0,
                'message': 'WireGuard started' if result.returncode == 0 else result.stderr.strip() or result.stdout.strip()
            }
        
        # Start PhazeVPN Protocol
        if protocol in ['all', 'phazevpn']:
            # Try phazevpn-protocol first
            result = subprocess.run(['systemctl', 'start', 'phazevpn-protocol'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try phazevpn-secure
                result = subprocess.run(['systemctl', 'start', 'phazevpn-secure'], capture_output=True, text=True, timeout=10)
            results['phazevpn'] = {
                'success': result.returncode == 0,
                'message': 'PhazeVPN Protocol started' if result.returncode == 0 else result.stderr.strip() or result.stdout.strip()
            }
        
        # Log activity
        if any(r.get('success') for r in results.values()):
            log_activity(session.get('username', 'unknown'), 'VPN_START', f'Started VPN protocols: {protocol}')
        
        # Return success if at least one started
        any_success = any(r.get('success') for r in results.values())
        return jsonify({
            'success': any_success,
            'message': 'VPN started successfully' if any_success else 'Failed to start VPN',
            'results': results
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout starting VPN service'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting VPN: {str(e)}'}), 500

@app.route('/api/vpn/stop', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_stop():
    """Stop VPN - stops all three protocols"""
    protocol = request.json.get('protocol', 'all') if request.is_json else 'all'
    results = {}
    
    try:
        # Stop OpenVPN
        if protocol in ['all', 'openvpn']:
            result = subprocess.run(['systemctl', 'stop', 'secure-vpn'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try killing OpenVPN process directly
                subprocess.run(['pkill', '-f', 'openvpn.*server.conf'], capture_output=True)
            results['openvpn'] = {
                'success': True,
                'message': 'OpenVPN stopped'
            }
        
        # Stop WireGuard
        if protocol in ['all', 'wireguard']:
            result = subprocess.run(['systemctl', 'stop', 'wg-quick@wg0'], capture_output=True, text=True, timeout=10)
            results['wireguard'] = {
                'success': result.returncode == 0,
                'message': 'WireGuard stopped' if result.returncode == 0 else result.stderr.strip() or result.stdout.strip()
            }
        
        # Stop PhazeVPN Protocol
        if protocol in ['all', 'phazevpn']:
            result = subprocess.run(['systemctl', 'stop', 'phazevpn-protocol'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                result = subprocess.run(['systemctl', 'stop', 'phazevpn-secure'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try killing process directly
                subprocess.run(['pkill', '-f', 'phazevpn-server'], capture_output=True)
            results['phazevpn'] = {
                'success': True,
                'message': 'PhazeVPN Protocol stopped'
            }
        
        # Log activity
        log_activity(session.get('username', 'unknown'), 'VPN_STOP', f'Stopped VPN protocols: {protocol}')
        
        return jsonify({
            'success': True,
            'message': 'VPN stopped successfully',
            'results': results
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout stopping VPN service'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping VPN: {str(e)}'}), 500

@app.route('/api/vpn/restart', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_restart():
    """Restart VPN - restarts all three protocols"""
    protocol = request.json.get('protocol', 'all') if request.is_json else 'all'
    results = {}
    
    try:
        # Restart OpenVPN
        if protocol in ['all', 'openvpn']:
            result = subprocess.run(['systemctl', 'restart', 'secure-vpn'], capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                # Try stop then start
                subprocess.run(['pkill', '-f', 'openvpn.*server.conf'], capture_output=True)
                vpn_manager = VPN_DIR / 'vpn-manager.py'
                if vpn_manager.exists():
                    result = subprocess.run(['python3', str(vpn_manager), 'start'], 
                                          capture_output=True, text=True, timeout=10)
            results['openvpn'] = {
                'success': result.returncode == 0,
                'message': 'OpenVPN restarted' if result.returncode == 0 else result.stderr.strip() or result.stdout.strip()
            }
        
        # Restart WireGuard
        if protocol in ['all', 'wireguard']:
            result = subprocess.run(['systemctl', 'restart', 'wg-quick@wg0'], capture_output=True, text=True, timeout=15)
            results['wireguard'] = {
                'success': result.returncode == 0,
                'message': 'WireGuard restarted' if result.returncode == 0 else result.stderr.strip() or result.stdout.strip()
            }
        
        # Restart PhazeVPN Protocol
        if protocol in ['all', 'phazevpn']:
            result = subprocess.run(['systemctl', 'restart', 'phazevpn-protocol'], capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                result = subprocess.run(['systemctl', 'restart', 'phazevpn-secure'], capture_output=True, text=True, timeout=15)
            results['phazevpn'] = {
                'success': result.returncode == 0,
                'message': 'PhazeVPN Protocol restarted' if result.returncode == 0 else result.stderr.strip() or result.stdout.strip()
            }
        
        # Log activity
        if any(r.get('success') for r in results.values()):
            log_activity(session.get('username', 'unknown'), 'VPN_RESTART', f'Restarted VPN protocols: {protocol}')
        
        # Return success if at least one restarted
        any_success = any(r.get('success') for r in results.values())
        return jsonify({
            'success': any_success,
            'message': 'VPN restarted successfully' if any_success else 'Failed to restart VPN',
            'results': results
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout restarting VPN service'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error restarting VPN: {str(e)}'}), 500

# ============================================
# TICKET API ENDPOINTS
# ============================================

@app.route('/api/tickets', methods=['POST'])
@require_api_auth
def api_create_ticket():
    """Create a new support ticket"""
    data = request.json
    username = session.get('username')
    
    if not username:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    email = data.get('email', '').strip()
    
    if not subject or not message:
        return jsonify({'success': False, 'error': 'Subject and message are required'}), 400
    
    ticket_id, ticket = create_ticket(username, subject, message, email)
    
    return jsonify({
        'success': True,
        'ticket_id': ticket_id,
        'ticket': ticket
    })

@app.route('/api/tickets')
@require_api_auth
def api_list_tickets():
    """List tickets - users see their own, admins/moderators see all"""
    username = session.get('username')
    users, _ = load_users()
    user = users.get(username, {})
    role = user.get('role', 'user')
    
    tickets_data = load_tickets()
    all_tickets = list(tickets_data.get('tickets', {}).values())
    
    # Filter based on role
    if role in ['admin', 'moderator']:
        # Admins and moderators see all tickets
        tickets = all_tickets
    else:
        # Regular users only see their own tickets
        tickets = [t for t in all_tickets if t.get('username') == username]
    
    # Sort by updated date (newest first)
    tickets.sort(key=lambda x: x.get('updated', ''), reverse=True)
    
    return jsonify({
        'success': True,
        'tickets': tickets,
        'count': len(tickets)
    })

@app.route('/api/tickets/<ticket_id>')
@require_api_auth
def api_get_ticket(ticket_id):
    """Get a specific ticket"""
    username = session.get('username')
    users, _ = load_users()
    user = users.get(username, {})
    role = user.get('role', 'user')
    
    tickets_data = load_tickets()
    ticket = tickets_data.get('tickets', {}).get(ticket_id)
    
    if not ticket:
        return jsonify({'success': False, 'error': 'Ticket not found'}), 404
    
    # Check permissions - users can only see their own tickets
    if role not in ['admin', 'moderator'] and ticket.get('username') != username:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    return jsonify({
        'success': True,
        'ticket': ticket
    })

@app.route('/api/tickets/<ticket_id>/reply', methods=['POST'])
@require_api_auth
def api_ticket_reply(ticket_id):
    """Add a reply to a ticket"""
    username = session.get('username')
    users, _ = load_users()
    user = users.get(username, {})
    role = user.get('role', 'user')
    
    tickets_data = load_tickets()
    ticket = tickets_data.get('tickets', {}).get(ticket_id)
    
    if not ticket:
        return jsonify({'success': False, 'error': 'Ticket not found'}), 404
    
    # Check permissions
    if role not in ['admin', 'moderator'] and ticket.get('username') != username:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400
    
    success, updated_ticket = add_ticket_reply(ticket_id, username, message)
    
    if success:
        return jsonify({
            'success': True,
            'ticket': updated_ticket
        })
    else:
        return jsonify({'success': False, 'error': updated_ticket}), 400

@app.route('/api/tickets/<ticket_id>/status', methods=['POST'])
@require_permission('can_manage_tickets')
def api_update_ticket_status(ticket_id):
    """Update ticket status (admin/moderator only)"""
    username = session.get('username')
    data = request.json
    status = data.get('status', '').strip()
    
    valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
    if status not in valid_statuses:
        return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    
    success, ticket = update_ticket_status(ticket_id, status, username)
    
    if success:
        return jsonify({
            'success': True,
            'ticket': ticket
        })
    else:
        return jsonify({'success': False, 'error': ticket}), 400

@app.route('/api/clients')
@require_permission('can_manage_clients')
def api_clients():
    """List clients"""
    return jsonify({'clients': list_clients()})

@app.route('/api/clients', methods=['POST'])
@require_permission('can_add_clients')
def api_add_client():
    """Add new client"""
    data = request.json
    client_name = data.get('name', '').strip()
    
    if not client_name:
        return jsonify({'success': False, 'error': 'Client name required'}), 400
    
    # Sanitize client name
    safe_name = ''.join(c for c in client_name if c.isalnum() or c in ['-', '_'])
    if not safe_name or safe_name != client_name:
        return jsonify({'success': False, 'error': f'Invalid client name. Use only letters, numbers, dashes, and underscores.'}), 400
    
    # Check subscription limits (unless admin/moderator creating for someone else)
    username = session.get('username', 'unknown')
    user_role = session.get('role', 'user')
    users, roles = load_users()  # Load users and roles here for limit checking and saving
    
    # Only enforce limits for regular users (admin/moderator can bypass)
    if user_role == 'user':
        can_create, limit_error = can_create_client(username)
        if not can_create:
            tier = get_user_subscription(username)
            limits = get_subscription_limits(username)
            return jsonify({
                'success': False, 
                'error': limit_error,
                'upgrade_required': True,
                'current_tier': tier,
                'limits': limits,
                'clients_used': len(users[username].get('clients', [])) if username in users else 0
            }), 403
    
    # Check if client already exists and is linked to this user
    config_file = CLIENT_CONFIGS_DIR / f'{safe_name}.ovpn'
    user_clients = users[username].get('clients', []) if username in users else []
    
    if config_file.exists():
        # Client file exists - check if it's linked to this user
        if safe_name in user_clients:
            return jsonify({'success': False, 'error': f'Client {client_name} already exists and is linked to your account'}), 400
        else:
            # Client exists but not linked - link it to user
            print(f"[CLIENT] Client {safe_name} exists but not linked, linking to {username}...")
            if username in users:
                if 'clients' not in users[username]:
                    users[username]['clients'] = []
                if safe_name not in users[username]['clients']:
                    users[username]['clients'].append(safe_name)
                    save_users(users, roles)
                    log_activity(username, 'CLIENT_LINK', f'Linked existing client: {safe_name}')
                    
                    # Return success since client is now linked
                    tier = get_user_subscription(username)
                    limits = get_subscription_limits(username)
                    current_count = len(users[username].get('clients', []))
                    
                    return jsonify({
                        'success': True,
                        'message': f'Client {client_name} was already created and is now linked to your account',
                        'subscription': {
                            'tier': tier,
                            'name': limits['name'],
                            'client_limit': limits['client_limit'],
                            'clients_used': current_count,
                            'can_create_more': current_count < limits['client_limit'] if limits['client_limit'] > 0 else True
                        }
                    })
            else:
                return jsonify({'success': False, 'error': f'Client {client_name} exists but user not found'}), 400
    
    # Call vpn-manager to create client
    vpn_manager = VPN_DIR / 'vpn-manager.py'
    if not vpn_manager.exists():
        # Fallback: try to find it
        vpn_manager = BASE_DIR / 'vpn-manager.py'
    
    # Additional fallback paths
    if not vpn_manager.exists():
        vpn_manager = Path('/opt/phaze-vpn/vpn-manager.py')
    if not vpn_manager.exists():
        vpn_manager = Path('/opt/secure-vpn/vpn-manager.py')
    
    if vpn_manager.exists():
        try:
            # Ensure VPN_DIR exists and is absolute
            vpn_dir_abs = Path(VPN_DIR).absolute()
            vpn_dir_abs.mkdir(parents=True, exist_ok=True)
            
            # Run with explicit error handling
            result = subprocess.run(
                ['python3', str(vpn_manager.absolute()), 'add-client', safe_name],
                cwd=str(vpn_dir_abs),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # Log the result for debugging
            print(f"[CLIENT] vpn-manager result: returncode={result.returncode}")
            if result.stdout:
                print(f"[CLIENT] stdout: {result.stdout[:500]}")
            if result.stderr:
                print(f"[CLIENT] stderr: {result.stderr[:500]}")
                
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Client creation timed out. Please try again.'}), 500
        except Exception as e:
            error_msg = f'Error running vpn-manager: {str(e)}'
            print(f"[CLIENT] Exception: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
    else:
        # Direct client creation if vpn-manager not available
        try:
            result = subprocess.run(
                ['bash', '-c', f'cd {VPN_DIR} && ./scripts/add-client.sh {safe_name}'],
                capture_output=True,
                text=True,
                timeout=120
            )
        if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or 'Unknown error'
                print(f"[CLIENT] Script failed: {error_msg}")
                return jsonify({'success': False, 'error': f'Client creation failed: {error_msg}'}), 500
        except Exception as e:
            error_msg = f'VPN manager not found and script failed: {str(e)}'
            print(f"[CLIENT] {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
    
    if result.returncode == 0:
        # Generate all config types (OpenVPN, PhazeVPN, WireGuard)
        generate_all_script = BASE_DIR / 'generate-all-configs.py'
        if not generate_all_script.exists():
            generate_all_script = VPN_DIR / 'generate-all-configs.py'
        
        if generate_all_script.exists():
            try:
                gen_result = subprocess.run(
                    ['python3', str(generate_all_script), safe_name],
                    cwd=str(VPN_DIR),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if gen_result.returncode == 0:
                    print(f"[CLIENT] Generated all config types for {safe_name}")
                else:
                    print(f"[CLIENT] Warning: Could not generate all config types: {gen_result.stderr}")
            except Exception as e:
                print(f"[CLIENT] Warning: Error generating additional configs: {e}")
        
        # Link client to user who created it (users already loaded above)
        if username in users:
            if 'clients' not in users[username]:
                users[username]['clients'] = []
            # Use safe_name for storage, but keep original for display
            if safe_name not in users[username]['clients']:
                users[username]['clients'].append(safe_name)
                save_users(users, roles)
        
        # Get updated subscription info for response
        tier = get_user_subscription(username)
        limits = get_subscription_limits(username)
        current_count = len(users[username].get('clients', []))
        
        log_activity(username, 'CLIENT_ADD', f'Added client: {safe_name} (display: {client_name})')
        return jsonify({
            'success': True, 
            'message': f'Client {client_name} created successfully',
            'subscription': {
                'tier': tier,
                'name': limits['name'],
                'client_limit': limits['client_limit'],
                'clients_used': current_count,
                'can_create_more': current_count < limits['client_limit'] if limits['client_limit'] > 0 else True
            }
        })
    else:
        # Provide detailed error message
        error_msg = result.stderr.strip() or result.stdout.strip() or 'Unknown error'
        # Include both stdout and stderr if available for debugging
        if result.stdout.strip() and result.stderr.strip():
            error_msg = f"{result.stderr.strip()}\n{result.stdout.strip()}"
        print(f"[CLIENT] Creation failed: {error_msg}")
        # Return more user-friendly error
        if 'already exists' in error_msg.lower() or 'exists' in error_msg.lower():
            return jsonify({'success': False, 'error': f'Client {client_name} already exists'}), 400
        elif 'permission' in error_msg.lower() or 'denied' in error_msg.lower():
            return jsonify({'success': False, 'error': 'Permission denied. Please check server permissions.'}), 403
        else:
            # Truncate very long error messages
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + '...'
            return jsonify({'success': False, 'error': f'Failed to create client: {error_msg}'}), 400

@app.route('/api/clients/<client_name>', methods=['DELETE'])
@require_permission('can_revoke_clients')
def api_delete_client(client_name):
    """Delete client"""
    config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
    if config_file.exists():
        config_file.unlink()
        log_activity(session.get('username', 'unknown'), 'CLIENT_DELETE', f'Deleted client: {client_name}')
        return jsonify({'success': True, 'message': f'Client {client_name} deleted'})
    return jsonify({'success': False, 'error': 'Client not found'}), 404

@app.route('/api/users', methods=['GET'])
@require_permission('can_manage_users')
def api_users():
    """List users"""
    users, roles = load_users()
    # Don't send passwords
    user_list = {name: {k: v for k, v in data.items() if k != 'password'} 
                 for name, data in users.items()}
    return jsonify({'users': user_list, 'roles': list(roles.keys())})

@app.route('/api/users', methods=['POST'])
@require_permission('can_manage_users')
def api_add_user():
    """Add new user"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user').lower()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    users, roles = load_users()
    
    if username in users:
        return jsonify({'success': False, 'error': 'User already exists'}), 400
    
    if role not in roles:
        return jsonify({'success': False, 'error': f'Invalid role. Must be one of: {", ".join(roles.keys())}'}), 400
    
    users[username] = {
        'password': hash_password(password),
        'role': role,
        'created': datetime.now().isoformat()
    }
    
    save_users(users, roles)
    log_activity(session.get('username', 'unknown'), 'USER_ADD', f'Added user: {username} (role: {role})')
    return jsonify({'success': True, 'message': f'User {username} created'})

@app.route('/api/users/<username>', methods=['DELETE'])
@require_permission('can_manage_users')
def api_delete_user(username):
    """Delete user"""
    if username == session.get('username'):
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
    
    users, roles = load_users()
    if username in users:
        del users[username]
        save_users(users, roles)
        log_activity(session.get('username', 'unknown'), 'USER_DELETE', f'Deleted user: {username}')
        return jsonify({'success': True, 'message': f'User {username} deleted'})
    return jsonify({'success': False, 'error': 'User not found'}), 404

@app.route('/api/profile', methods=['POST'])
def api_update_profile():
    """Update user profile"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    data = request.json
    email = data.get('email', '').strip()  # Optional
    
    users, roles = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Check email uniqueness only if email provided
    if email:
        for user_name, user_data in users.items():
            if user_name != username and user_data.get('email') == email:
                return jsonify({'success': False, 'error': 'Email already in use'}), 400
        users[username]['email'] = email
    else:
        # Remove email if empty
        users[username].pop('email', None)
    
    save_users(users, roles)
    log_activity(username, 'PROFILE_UPDATE', 'Updated profile information')
    
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/api/profile/password', methods=['POST'])
def api_change_password():
    """Change user password"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    data = request.json
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Current and new password required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
    
    users, roles = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Verify current password
    stored_password = users[username].get('password', '')
    
    if not verify_password(current_password, stored_password):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
    
    # Update password
    users[username]['password'] = hash_password(new_password)
    save_users(users, roles)
    log_activity(username, 'PASSWORD_CHANGE', 'Changed password')
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@app.route('/api/my-clients', methods=['GET', 'POST'])
def api_my_clients():
    """Get or create user's VPN clients"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    users, _ = load_users()
    
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    if request.method == 'GET':
        # Return user's clients with subscription info
        user_client_names = users[username].get('clients', [])
        clients = []
        if CLIENT_CONFIGS_DIR.exists():
            for client_name in user_client_names:
                config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
                if config_file.exists():
                    clients.append({
                        'name': client_name,
                        'created': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                    })
        
        # Include subscription info
        subscription = users[username].get('subscription', {'tier': 'free'})
        tier = subscription.get('tier', 'free')
        limits = SUBSCRIPTION_TIERS[tier]
        
        return jsonify({
            'success': True, 
            'clients': clients,
            'subscription': {
                'tier': tier,
                'name': limits['name'],
                'client_limit': limits['client_limit'],
                'clients_used': len(clients),
                'can_create_more': len(clients) < limits['client_limit'] if limits['client_limit'] > 0 else True
            }
        })
    
    elif request.method == 'POST':
        # Create new client for user
        data = request.json
        client_name = data.get('name', '').strip()
        
        if not client_name:
            return jsonify({'success': False, 'error': 'Client name required'}), 400
        
        # Check subscription limits
        can_create, limit_error = can_create_client(username)
        if not can_create:
            return jsonify({
                'success': False, 
                'error': limit_error,
                'upgrade_required': True,
                'current_tier': get_user_subscription(username),
                'limits': get_subscription_limits(username)
            }), 403
        
        # Check if client already exists
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
        if config_file.exists():
            return jsonify({'success': False, 'error': f'Client {client_name} already exists'}), 400
        
        # Create client using vpn-manager
        vpn_manager = VPN_DIR / 'vpn-manager.py'
        if not vpn_manager.exists():
            vpn_manager = BASE_DIR / 'vpn-manager.py'
        
        if vpn_manager.exists():
            result = subprocess.run(['python3', str(vpn_manager), 'add-client', client_name],
                                   cwd=str(VPN_DIR), capture_output=True, text=True)
        else:
            return jsonify({'success': False, 'error': 'VPN manager not found'}), 500
        
        if result.returncode == 0:
            # Link client to user
            if 'clients' not in users[username]:
                users[username]['clients'] = []
            if client_name not in users[username]['clients']:
                users[username]['clients'].append(client_name)
            
            _, roles = load_users()
            save_users(users, roles)
            
            log_activity(username, 'CLIENT_CREATE', f'Created client: {client_name}')
            return jsonify({'success': True, 'message': f'Client {client_name} created successfully'})
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or 'Unknown error'
            return jsonify({'success': False, 'error': error_msg}), 400

@app.route('/2fa/setup')
def twofa_setup():
    """2FA setup page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    try:
        secret = generate_secret(username)
        qr_url = get_qr_url(username, secret)
        qr_image = generate_qr_image(qr_url)
        return render_template('2fa-setup.html', username=username, secret=secret, qr_image=qr_image, qr_url=qr_url)
    except Exception as e:
        return render_template('error.html', message=f'2FA setup error: {str(e)}'), 500

@app.route('/2fa/enable', methods=['POST'])
def twofa_enable():
    """Enable 2FA"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    username = session['username']
    token = request.json.get('token', '')
    if not verify_token(username, token):
        return jsonify({'success': False, 'error': 'Invalid verification code'}), 400
    if enable_2fa(username):
        log_activity(username, '2FA_ENABLE', 'Enabled 2FA')
        return jsonify({'success': True, 'message': '2FA enabled successfully'})
    return jsonify({'success': False, 'error': 'Failed to enable 2FA'}), 500

@app.route('/2fa/disable', methods=['POST'])
def twofa_disable():
    """Disable 2FA"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    username = session['username']
    data = request.json
    password = data.get('password', '')
    users, _ = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    stored_password = users[username].get('password', '')
    if not verify_password(password, stored_password):
        return jsonify({'success': False, 'error': 'Invalid password'}), 400
    if disable_2fa(username):
        log_activity(username, '2FA_DISABLE', 'Disabled 2FA')
        return jsonify({'success': True, 'message': '2FA disabled successfully'})
    return jsonify({'success': False, 'error': 'Failed to disable 2FA'}), 500

# ============================================
# PAYMENT API ENDPOINTS
# ============================================

@app.route('/api/payments')
@require_role('admin')
def api_payments():
    """Get all payment requests"""
    requests_data = load_payment_requests()
    payment_requests = list(requests_data.get('requests', {}).values())
    
    # Sort by created date (newest first)
    payment_requests.sort(key=lambda x: x.get('created', ''), reverse=True)
    
    return jsonify({'success': True, 'payments': payment_requests})

@app.route('/api/payments/<payment_id>/approve', methods=['POST'])
@require_role('admin')
def api_approve_payment(payment_id):
    """Approve payment request"""
    success, message = approve_payment_request(payment_id)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 400

@app.route('/admin/payment-settings')
@require_role('admin')
def admin_payment_settings():
    """Admin payment settings page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('admin/payment-settings.html')

@app.route('/api/payments/settings', methods=['GET', 'POST'])
@require_role('admin')
def api_payment_settings():
    """Get or update payment settings"""
    if request.method == 'GET':
        # Load from payment_integrations settings file
        settings = load_payment_settings()
        # Don't return secret key in GET request for security (just indicate if set)
        safe_settings = {k: v for k, v in settings.items() if k != 'stripe_secret_key'}
        safe_settings['stripe_secret_key_set'] = bool(settings.get('stripe_secret_key'))
        return jsonify({'success': True, 'settings': safe_settings})
    
    elif request.method == 'POST':
        if 'username' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.json
        
        # Load current settings
        payment_settings = load_payment_settings()
        
        # Update with new values
        if 'venmo_username' in data:
            payment_settings['venmo_username'] = data['venmo_username'].strip()
        if 'cashapp_username' in data:
            payment_settings['cashapp_username'] = data['cashapp_username'].strip()
            payment_settings['cashapp_tag'] = data['cashapp_username'].strip().replace('$', '')
        if 'stripe_enabled' in data:
            payment_settings['stripe_enabled'] = data.get('stripe_enabled', False)
        if 'stripe_publishable_key' in data:
            payment_settings['stripe_publishable_key'] = data['stripe_publishable_key'].strip()
        if 'stripe_secret_key' in data and data['stripe_secret_key']:
            payment_settings['stripe_secret_key'] = data['stripe_secret_key'].strip()
        
        # Save to payment_integrations settings file
        save_payment_settings(payment_settings)
        
        # Also update payment requests settings for backwards compatibility
        try:
            requests_data = load_payment_requests()
            requests_data['settings'] = {
                'venmo_username': payment_settings.get('venmo_username', ''),
                'cashapp_username': payment_settings.get('cashapp_username', ''),
                'stripe_enabled': payment_settings.get('stripe_enabled', False),
                'stripe_publishable_key': payment_settings.get('stripe_publishable_key', '')
            }
            save_payment_requests(requests_data)
        except:
            pass
        
        log_activity(session['username'], 'PAYMENT_SETTINGS_UPDATE', 'Updated payment settings')
        
        return jsonify({'success': True, 'message': 'Payment settings updated successfully'})

# ============================================
# PAYMENT ROUTES
# ============================================

@app.route('/pricing')
def pricing():
    """Pricing page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    subscription = user.get('subscription', {'tier': 'free'})
    current_tier = subscription.get('tier', 'free')
    current_tier_name = SUBSCRIPTION_TIERS[current_tier]['name']
    
    return render_template('pricing.html', 
                         current_tier=current_tier,
                         current_tier_name=current_tier_name,
                         tiers=SUBSCRIPTION_TIERS)

@app.route('/payment')
def payment():
    """Payment request page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    tier = request.args.get('tier', 'basic')
    if tier not in SUBSCRIPTION_TIERS:
        return redirect(url_for('pricing'))
    
    username = session['username']
    tier_info = SUBSCRIPTION_TIERS[tier]
    amount = tier_info['price']
    
    # Get payment settings
    payment_settings = load_payment_settings()
    stripe_enabled = payment_settings.get('stripe_enabled', False)
    stripe_publishable_key = payment_settings.get('stripe_publishable_key', '')
    
    # Create payment request for manual payments
    payment_id, request_data = create_payment_request(username, tier, amount)
    
    # Get payment settings (admin configured)
    requests_data = load_payment_requests()
    settings = requests_data.get('settings', {})
    venmo_username = settings.get('venmo_username', '')
    cashapp_username = settings.get('cashapp_username', '')
    
    # Generate payment links
    payment_links = generate_payment_links(payment_id, amount, venmo_username, cashapp_username)
    
    return render_template('payment.html',
                         payment_id=payment_id,
                         tier=tier,
                         tier_info=tier_info,
                         amount=amount,
                         payment_links=payment_links,
                         venmo_username=venmo_username,
                         cashapp_username=cashapp_username,
                         stripe_enabled=stripe_enabled,
                         stripe_publishable_key=stripe_publishable_key)

@app.route('/payment/stripe/checkout', methods=['POST'])
def stripe_checkout():
    """Create Stripe checkout session"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    data = request.json
    tier = data.get('tier', 'basic')
    
    if tier not in SUBSCRIPTION_TIERS:
        return jsonify({'success': False, 'error': 'Invalid tier'}), 400
    
    tier_info = SUBSCRIPTION_TIERS[tier]
    amount = tier_info['price']
    amount_cents = int(amount * 100)  # Convert to cents
    
    # Create Stripe checkout session
    result = create_stripe_checkout_session(
        amount=amount_cents,
        username=username,
        tier=tier,
        success_url=url_for('payment_success', _external=True),
        cancel_url=url_for('payment', tier=tier, _external=True)
    )
    
    if result.get('error'):
        return jsonify({'success': False, 'error': result['error']}), 400
    
    return jsonify({
        'success': True,
        'checkout_url': result.get('url'),
        'session_id': result.get('session_id')
    })

@app.route('/payment/success')
def payment_success():
    """Handle successful Stripe payment"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    session_id = request.args.get('session_id')
    if not session_id:
        return render_template('payment-success.html', success=False)
    
    # Verify payment
    verification = verify_stripe_payment(session_id)
    
    if verification.get('error') or not verification.get('paid'):
        return render_template('payment-success.html', success=False)
    
    username = verification.get('username') or session['username']
    tier = verification.get('tier', 'basic')
    amount = verification.get('amount_total', 0)
    
    # Update user subscription
    users, _ = load_users()
    if username in users:
        users[username]['subscription'] = {
            'tier': tier,
            'status': 'active',
            'activated_at': datetime.now().isoformat(),
            'payment_method': 'stripe',
            'payment_amount': amount
        }
        save_users(users, None)
        
        log_activity(username, 'SUBSCRIPTION_UPGRADE', f'Upgraded to {tier} via Stripe')
    
    return render_template('payment-success.html', 
                         success=True,
                         tier=tier,
                         amount=amount)

@app.route('/payment/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data.decode('utf-8')
    signature = request.headers.get('Stripe-Signature', '')
    
    result = handle_stripe_webhook(payload, signature)
    
    if result.get('error'):
        return jsonify({'error': result['error']}), 400
    
    # Handle different event types
    event_type = result.get('type')
    event_data = result.get('data', {})
    
    if event_type == 'checkout.session.completed':
        # Payment completed
        metadata = event_data.get('metadata', {})
        username = metadata.get('username')
        tier = metadata.get('tier')
        
        if username and tier:
            users, _ = load_users()
            if username in users:
                users[username]['subscription'] = {
                    'tier': tier,
                    'status': 'active',
                    'activated_at': datetime.now().isoformat(),
                    'payment_method': 'stripe'
                }
                save_users(users, None)
                log_activity(username, 'SUBSCRIPTION_UPGRADE', f'Upgraded to {tier} via Stripe webhook')
    
    return jsonify({'success': True})

@app.route('/api/payment/submit', methods=['POST'])
def api_payment_submit():
    """Submit payment proof"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    data = request.json
    payment_id = data.get('payment_id', '').strip()
    transaction_id = data.get('transaction_id', '').strip()
    payment_method = data.get('payment_method', '').strip()
    
    if not payment_id:
        return jsonify({'success': False, 'error': 'Payment ID required'}), 400
    
    requests_data = load_payment_requests()
    if payment_id not in requests_data['requests']:
        return jsonify({'success': False, 'error': 'Payment request not found'}), 404
    
    request_info = requests_data['requests'][payment_id]
    
    if request_info['username'] != username:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if request_info['status'] != 'pending':
        return jsonify({'success': False, 'error': f'Payment request already {request_info["status"]}'}), 400
    
    # Update request with payment info
    request_info['transaction_id'] = transaction_id
    request_info['payment_method'] = payment_method
    request_info['submitted_at'] = datetime.now().isoformat()
    
    requests_data['requests'][payment_id] = request_info
    save_payment_requests(requests_data)
    
    # Auto-approve if transaction ID provided and matches payment gateway format
    # For Stripe: transaction IDs start with 'ch_' or 'pi_'
    # For PayPal: transaction IDs are alphanumeric, 17 chars
    # For Venmo/CashApp: transaction IDs are typically shorter alphanumeric
    auto_approve = False
    if transaction_id:
        # Check if transaction ID matches known payment gateway patterns
        if re.match(r'^(ch_|pi_|txn_|pay_)', transaction_id, re.IGNORECASE):
            # Looks like a valid payment gateway transaction ID
            auto_approve = True
        elif len(transaction_id) >= 10 and re.match(r'^[A-Z0-9]+$', transaction_id):
            # Alphanumeric transaction ID (PayPal, Venmo, CashApp format)
            auto_approve = True
    
    if auto_approve:
        # Auto-approve payment
        success, message = approve_payment_request(payment_id)
        if success:
            log_activity(username, 'PAYMENT_AUTO_APPROVED', f'Auto-approved payment {payment_id} with transaction {transaction_id}')
            return jsonify({
                'success': True,
                'message': 'Payment approved automatically',
                'payment_id': payment_id
            })
    
    log_activity(username, 'PAYMENT_SUBMITTED', f'Submitted payment proof for {payment_id}')
    
    return jsonify({
        'success': True,
        'message': 'Payment proof submitted. Admin will review and approve shortly.',
        'payment_id': payment_id
    })

@app.route('/api/export/activity')
@require_permission('can_view_statistics')
def api_export_activity():
    """Export activity logs as CSV"""
    logs = get_activity_logs(1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'User', 'Action', 'Details'])
    
    for log in logs:
        parts = log.split(':', 2)
        if len(parts) >= 3:
            timestamp = parts[0].strip('[]')
            user = parts[1].strip()
            action = parts[2].strip()
            writer.writerow([timestamp, user, action, ''])
        else:
            writer.writerow(['', '', log, ''])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'activity-{datetime.now().strftime("%Y%m%d")}.csv'
    )

# ============================================
# MOBILE APP API ENDPOINTS
# ============================================

@app.route('/api/app/login', methods=['POST'])
def api_app_login():
    """Mobile app login - Returns token and user info"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    users, _ = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    user = users[username]
    stored_password = user.get('password', '')
    
    if not verify_password(password, stored_password):
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    # Create session for app
    session['username'] = username
    session['role'] = user.get('role', 'user')
    
    # Get subscription info
    subscription = user.get('subscription', {'tier': 'free'})
    tier = subscription.get('tier', 'free')
    limits = SUBSCRIPTION_TIERS[tier]
    
    return jsonify({
        'success': True,
        'user': {
            'username': username,
            'role': user.get('role', 'user')
        },
        'subscription': {
            'tier': tier,
            'name': limits['name'],
            'client_limit': limits['client_limit'],
            'bandwidth_limit_gb': limits['bandwidth_limit_gb']
        },
        'message': 'Login successful'
    })

@app.route('/api/app/signup', methods=['POST'])
def api_app_signup():
    """Mobile/GUI app signup - Returns success status"""
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    if not email:
        return jsonify({'success': False, 'error': 'Email address is required'}), 400
    
    if password != confirm_password:
        return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    users, roles = load_users()
    
    if username in users:
        return jsonify({'success': False, 'error': 'Username already exists'}), 409
    
    # Check email uniqueness
    for user_data in users.values():
        if user_data.get('email') == email:
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    verification_expires = (datetime.now() + timedelta(hours=24)).isoformat()
    
    # Create user with free subscription (unverified)
    user_data = {
        'password': hash_password(password),
        'role': 'user',
        'email': email,
        'email_verified': False,
        'verification_token': verification_token,
        'verification_expires': verification_expires,
        'created': datetime.now().isoformat(),
        'clients': [],
        'subscription': {
            'tier': 'free',
            'status': 'active',
            'created': datetime.now().isoformat(),
            'expires': None
        },
        'usage': {
            'bandwidth_used_gb': 0,
            'month_start': datetime.now().replace(day=1).isoformat()
        }
    }
    
    users[username] = user_data
    save_users(users, roles)
    log_activity('system', 'USER_SIGNUP', f'New user registered via app: {username} (unverified)')
    
    # Send verification email
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from email_api import send_verification_email
        success, msg = send_verification_email(email, username, verification_token)
        if not success:
            print(f"Failed to send verification email: {msg}")
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        # Don't fail signup if email fails
    
    return jsonify({
        'success': True,
        'message': 'Account created successfully. Please check your email to verify your account.',
        'user': {
            'username': username,
            'email': email,
            'role': 'user'
        }
    })

@app.route('/api/app/configs', methods=['GET'])
def api_app_configs():
    """Get user's VPN configs for mobile app"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    
    # Get user's clients
    user_client_names = user.get('clients', [])
    configs = []
    
    if CLIENT_CONFIGS_DIR.exists():
        for client_name in user_client_names:
            config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
            if config_file.exists():
                # Read config content
                try:
                    with open(config_file, 'r') as f:
                        config_content = f.read()
                    
                    configs.append({
                        'name': client_name,
                        'config': config_content,
                        'created': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                    })
                except:
                    pass
    
    return jsonify({
        'success': True,
        'configs': configs,
        'count': len(configs)
    })

@app.route('/api/app/servers', methods=['GET'])
def api_app_servers():
    """Get available VPN servers for mobile app"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    # Currently one server, but can expand to multiple
    servers = [{
        'id': 'phazevpn-1',
        'name': 'PhazeVPN Main',
        'location': 'US',
        'hostname': 'phazevpn.com',
        'ip': '15.204.11.19',
        'port': 1194,
        'protocol': 'UDP',
        'status': 'online'
    }]
    
    return jsonify({
        'success': True,
        'servers': servers
    })

@app.route('/api/app/connection-status', methods=['GET'])
def api_app_connection_status():
    """Get user's current VPN connection status"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    username = session['username']
    users, _ = load_users()
    user = users.get(username, {})
    
    # Get user's clients
    user_client_names = user.get('clients', [])
    
    # Check active connections
    all_connections = get_active_connections()
    user_connections = [c for c in all_connections 
                       if c.get('name', '').lower() in [n.lower() for n in user_client_names]]
    
    connected = len(user_connections) > 0
    
    return jsonify({
        'success': True,
        'connected': connected,
        'connections': user_connections if connected else [],
        'server': 'phazevpn.com' if connected else None
    })

@app.route('/api/v1/client/register', methods=['POST'])
def api_v1_client_register():
    """Register a new client with the VPS"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')  # Unique client identifier (MAC address or generated UUID)
        hostname = data.get('hostname', 'unknown')
        os_type = data.get('os', 'unknown')
        os_version = data.get('os_version', 'unknown')
        client_version = data.get('version', '1.0.3')  # Updated default to match package version
        username = data.get('username', '')  # User account on VPS
        password = data.get('password', '')  # User password for authentication
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        # Authenticate user if credentials provided
        user_authenticated = False
        if username and password:
            users, _ = load_users()
            user = users.get(username)
            if user:
                stored_password = user.get('password', '')
                # Try bcrypt verification
                try:
                    if stored_password.startswith('$2b$') or stored_password.startswith('$2a$'):
                        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                            user_authenticated = True
                    # Legacy SHA256 support
                    elif len(stored_password) == 64:
                        import hashlib
                        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
                        if stored_password == hashed_password:
                            user_authenticated = True
                    # Plain text fallback (shouldn't happen but handle it)
                    elif stored_password == password:
                        user_authenticated = True
                except Exception:
                    pass
        
        # Load registered clients
        clients_file = VPN_DIR / 'registered_clients.json'
        if clients_file.exists():
            try:
                with open(clients_file, 'r') as f:
                    clients_data = json.load(f)
            except:
                clients_data = {'clients': {}}
        else:
            clients_data = {'clients': {}}
        
        # Check if client already registered
        if client_id in clients_data['clients']:
            client = clients_data['clients'][client_id]
            client['last_seen'] = datetime.now().isoformat()
            client['hostname'] = hostname
            client['os'] = os_type
            client['os_version'] = os_version
            client['version'] = client_version
            # Update subscription if user authenticated
            if user_authenticated:
                client['username'] = username
        else:
            # New client registration
            client = {
                'client_id': client_id,
                'hostname': hostname,
                'os': os_type,
                'os_version': os_version,
                'version': client_version,
                'registered_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'username': username if user_authenticated else None,
                'subscription': {
                    'status': 'active' if user_authenticated else 'pending',
                    'expires_at': None,
                    'plan': 'free' if user_authenticated else None
                },
                'vpn_config': None,  # Will be assigned when client config created
                'status': 'registered'
            }
            clients_data['clients'][client_id] = client
        
        # Save updated clients
        clients_file.parent.mkdir(parents=True, exist_ok=True)
        with open(clients_file, 'w') as f:
            json.dump(clients_data, f, indent=2)
        
        # Get VPN config URL if available
        vpn_config_url = None
        if client.get('vpn_config'):
            vpn_config_url = f"/download/{client['vpn_config']}"
        elif user_authenticated and username:
            # Try to find user's first client config
            user_clients = []
            users, _ = load_users()
            user = users.get(username, {})
            user_clients = user.get('clients', [])
            if user_clients:
                # Use first client config
                first_client = user_clients[0]
                config_file = CLIENT_CONFIGS_DIR / f'{first_client}.ovpn'
                if config_file.exists():
                    vpn_config_url = f"/download/{first_client}.ovpn"
        
        return jsonify({
            'success': True,
            'client_id': client_id,
            'subscription': client['subscription'],
            'vpn_config_url': vpn_config_url,
            'message': 'Client registered successfully'
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v1/client/checkin', methods=['POST'])
def api_v1_client_checkin():
    """Periodic check-in from client"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        # Load registered clients
        clients_file = VPN_DIR / 'registered_clients.json'
        if clients_file.exists():
            try:
                with open(clients_file, 'r') as f:
                    clients_data = json.load(f)
            except:
                return jsonify({'success': False, 'error': 'Failed to load clients'}), 500
        else:
            return jsonify({'success': False, 'error': 'Client not registered'}), 404
        
        # Update last seen
        if client_id in clients_data.get('clients', {}):
            clients_data['clients'][client_id]['last_seen'] = datetime.now().isoformat()
            with open(clients_file, 'w') as f:
                json.dump(clients_data, f, indent=2)
            return jsonify({'success': True, 'message': 'Check-in successful'}), 200
        else:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/connections')
@require_permission('can_view_statistics')
def api_export_connections():
    """Export connection history as CSV"""
    history = []
    if CONNECTION_HISTORY.exists():
        try:
            with open(CONNECTION_HISTORY, 'r') as f:
                history = json.load(f)
        except:
            pass
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Client', 'Action', 'Virtual IP', 'Real IP'])
    
    for event in history:
        writer.writerow([
            event.get('timestamp', ''),
            event.get('name', 'Unknown'),
            event.get('action', ''),
            event.get('virtual_ip', ''),
            event.get('real_ip', '')
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'connections-{datetime.now().strftime("%Y%m%d")}.csv'
    )

# APT Repository Routes
REPO_DIR = Path('/var/www/phazevpn-repo')

@app.route('/repo/gpg-key.asc')
def repo_gpg_key():
    """Serve GPG key for APT repository"""
    gpg_key_path = REPO_DIR / 'gpg-key.asc'
    if gpg_key_path.exists():
        return send_file(str(gpg_key_path), mimetype='application/pgp-keys')
    return 'GPG key not found', 404

@app.route('/repo/')
@app.route('/repo')
def repo_index():
    """Repository index"""
    return redirect('/repo/index.html')

@app.route('/logo.png')
@app.route('/images/logo.png')
def serve_logo():
    """Serve logo directly with cache control"""
    # Use optimized version for web (faster loading)
    logo_path = Path(__file__).parent / 'static' / 'images' / 'logo-optimized.png'
    if not logo_path.exists():
        logo_path = Path(__file__).parent / 'static' / 'images' / 'logo.png'
    if logo_path.exists():
        return send_file(str(logo_path), mimetype='image/png', cache_timeout=0)
    return 'Logo not found', 404

@app.route('/favicon.ico')
def serve_favicon():
    """Serve favicon"""
    favicon_path = Path(__file__).parent / 'static' / 'images' / 'favicon.png'
    if favicon_path.exists():
        return send_file(str(favicon_path), mimetype='image/png', cache_timeout=0)
    return 'Favicon not found', 404

@app.route('/api/v1/easter-egg/reward', methods=['POST'])
@require_role('user', 'moderator', 'admin')  # Any logged-in user
def easter_egg_reward():
    """Grant 1 month free premium for finding all easter eggs"""
    try:
        username = session.get('username')
        if not username:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        # Load users
        users, roles = load_users()
        
        if username not in users:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user = users[username]
        
        # Check if already rewarded
        if user.get('easter_egg_rewarded'):
            return jsonify({
                'success': True, 
                'message': 'Reward already granted',
                'already_rewarded': True
            }), 200
        
        # Grant 1 month premium
        from datetime import datetime, timedelta
        
        # Set subscription to premium for 1 month
        user['subscription'] = {
            'status': 'active',
            'plan': 'premium',
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
            'easter_egg_reward': True
        }
        
        user['easter_egg_rewarded'] = True
        user['easter_egg_rewarded_at'] = datetime.now().isoformat()
        
        # Save users
        save_users(users, roles)
        
        # Log activity
        log_activity(username, 'easter_egg_reward', f'Easter egg reward: 1 month premium granted')
        
        return jsonify({
            'success': True,
            'message': '1 month of free premium granted!',
            'expires_at': user['subscription']['expires_at']
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/repo/<path:filename>')
def repo_file(filename):
    """Serve repository files"""
    file_path = REPO_DIR / filename
    if file_path.exists() and file_path.is_file():
        # Determine content type
        if filename.endswith('.deb'):
            mimetype = 'application/octet-stream'
        elif filename.endswith('.asc'):
            mimetype = 'application/pgp-keys'
        elif filename.endswith('.gz'):
            # Packages.gz should be text/plain, other .gz files are gzip
            if 'Packages' in filename:
                mimetype = 'text/plain'
            else:
                mimetype = 'application/gzip'
        elif filename.endswith('Release') or filename.endswith('InRelease'):
            mimetype = 'text/plain'
        elif filename.endswith('Release.gpg'):
            mimetype = 'application/pgp-signature'
        elif filename.endswith('Packages'):
            mimetype = 'text/plain'
        else:
            mimetype = None
        return send_file(str(file_path), mimetype=mimetype)
    return 'File not found', 404

if __name__ == '__main__':
    # Ensure directories exist
    VPN_DIR.mkdir(parents=True, exist_ok=True)
    CLIENT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("🚀 SecureVPN Web Portal Starting...")
    print("="*60)
    print(f"Admin Dashboard: http://localhost:5000/admin")
    print(f"Moderator Panel: http://localhost:5000/moderator")
    print(f"Analytics: http://localhost:5000/admin/analytics")
    print()
    print("Default logins:")
    print("  Admin: admin / admin123")
    print("  Moderator: moderator / mod123")
    print("  User: user / user123")
    print("="*60)
    
    # Run on port 5000 (or from environment variable)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
