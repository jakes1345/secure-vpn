#!/usr/bin/env python3
"""
Simple HTTP server for clients to download their VPN configs
Run with: python3 client-download-server.py
Access at: http://YOUR_SERVER_IP:8081
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
from pathlib import Path
import sys
import json
import time
import traceback
import importlib.util

# Lazy import for PhazeVPN config generation (only when needed)
# This prevents crashes if phazevpn-protocol module doesn't exist
PHAZEVPN_PROTOCOL_AVAILABLE = False
generate_phazevpn_config = None

def load_phazevpn_module():
    """Lazy load PhazeVPN protocol module - only when needed"""
    global PHAZEVPN_PROTOCOL_AVAILABLE, generate_phazevpn_config
    
    if PHAZEVPN_PROTOCOL_AVAILABLE:
        return generate_phazevpn_config
    
    try:
        phazevpn_protocol_path = Path(__file__).parent / "phazevpn-protocol"
        
        # Try different possible filenames
        possible_files = [
            "generate-phazevpn-config.py",  # Actual filename (with hyphens)
            "generate_phazevpn_config.py",  # Python-friendly name
        ]
        
        config_file = None
        for filename in possible_files:
            test_path = phazevpn_protocol_path / filename
            if test_path.exists():
                config_file = test_path
                break
        
        if not config_file:
            print(f"Warning: PhazeVPN protocol module not found in {phazevpn_protocol_path}")
            return None
        
        # Load module dynamically (handles hyphens in filename)
        spec = importlib.util.spec_from_file_location("generate_phazevpn_config", config_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            generate_phazevpn_config = getattr(module, 'generate_phazevpn_config', None)
            if generate_phazevpn_config:
                PHAZEVPN_PROTOCOL_AVAILABLE = True
                print(f"✅ Loaded PhazeVPN protocol module from {config_file.name}")
                return generate_phazevpn_config
        
        print(f"Warning: Could not load generate_phazevpn_config from {config_file}")
        return None
    except Exception as e:
        print(f"Warning: Could not load PhazeVPN protocol module: {e}")
        import traceback
        traceback.print_exc()
        return None

VPN_DIR = Path(__file__).parent
CLIENT_CONFIGS_DIR = VPN_DIR / 'client-configs'
PORT = 8081

# Security: Set to True to require authentication tokens for downloads
# When False, anyone can download any client config (less secure but easier)
# DISABLED by default - simple client name download (more user-friendly)
REQUIRE_AUTHENTICATION = os.environ.get('REQUIRE_DOWNLOAD_AUTH', 'false').lower() == 'true'

# Path to users.json (shared with web portal)
USERS_FILE = VPN_DIR / 'users.json'

class ConfigDownloadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Handle OPTIONS requests for CORS
        if self.command == 'OPTIONS':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            return
        
        if path == '/' or path == '/index.html':
            self.serve_index()
        elif path == '/download':
            self.handle_download(parsed_path)
        elif path == '/list':
            self.list_configs()
        elif path == '/clients':
            self.serve_clients_page()
        else:
            self.send_error(404, "Not Found")
    
    def serve_index(self):
        """Serve the download page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>PhazeVPN Client Download</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            color: #333;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        .config-options {
            margin: 20px 0;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
        }
        .config-option {
            margin: 10px 0;
            padding: 12px;
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .config-option:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .config-option.selected {
            border-color: #667eea;
            background: #e3f2fd;
        }
        .config-option input[type="radio"] {
            width: auto;
            margin-right: 10px;
        }
        .config-option label {
            margin: 0;
            cursor: pointer;
            font-weight: 500;
        }
        .config-description {
            font-size: 13px;
            color: #666;
            margin-top: 5px;
            margin-left: 28px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .info {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
            font-size: 14px;
            color: #1976d2;
        }
        .error {
            background: #ffebee;
            border-left: 4px solid #f44336;
            padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
            font-size: 14px;
            color: #c62828;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 PhazeVPN Client Download</h1>
        <p class="subtitle">Choose your device type and download configuration</p>
        
        <div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
            <strong>✅ Simple Download:</strong> Just enter your client name below and download your config. 
            No login required - quick and easy!
        </div>
        
        <form onsubmit="downloadConfig(event)">
            <div class="form-group">
                <label for="clientName">Client Name:</label>
                <input type="text" id="clientName" name="clientName" 
                       placeholder="Enter client name (e.g., 'admin' not 'admin.ovpn')" required autofocus>
                <div style="font-size: 12px; color: #666; margin-top: 5px; padding-left: 5px;">
                    💡 <strong>Tip:</strong> Enter just the client name. Don't include file extensions like .ovpn or .phazevpn
                </div>
            </div>
            
            <div class="config-options">
                <label style="font-weight: 600; margin-bottom: 10px; display: block;">Select Configuration Type:</label>
                
                <div class="config-option" onclick="selectConfig('openvpn')">
                    <input type="radio" id="config-openvpn" name="configType" value="openvpn" checked>
                    <label for="config-openvpn">📱 OpenVPN Config (.ovpn) - For Mobile Devices</label>
                    <div class="config-description">
                        Use with OpenVPN Connect app on iPhone, iPad, or Android devices
                    </div>
                </div>
                
                <div class="config-option" onclick="selectConfig('phazevpn')">
                    <input type="radio" id="config-phazevpn" name="configType" value="phazevpn">
                    <label for="config-phazevpn">💻 PhazeVPN Protocol Config (.phazevpn) - For Desktop</label>
                    <div class="config-description">
                        Use with PhazeVPN Client app on Windows, Mac, or Linux
                    </div>
                </div>
                
                <div class="config-option" onclick="selectConfig('wireguard')">
                    <input type="radio" id="config-wireguard" name="configType" value="wireguard">
                    <label for="config-wireguard">🎮 WireGuard Config (.conf) - For Gaming/Streaming</label>
                    <div class="config-description">
                        Fastest option! Use with WireGuard app (2-3x faster than OpenVPN)
                    </div>
                </div>
                
                <div class="config-option" onclick="selectConfig('both')">
                    <input type="radio" id="config-both" name="configType" value="both">
                    <label for="config-both">📦 Download All Configurations</label>
                    <div class="config-description">
                        Download OpenVPN, PhazeVPN, and WireGuard configs for maximum compatibility
                    </div>
                </div>
            </div>
            
            <button type="submit" id="downloadBtn">📥 Download Config</button>
        </form>
        
        <div id="message"></div>
        
        <div class="info">
            <strong>Instructions:</strong><br>
            1. Enter your client name (just the name, like "admin" - not "admin.ovpn")<br>
            2. Select which configuration type you need<br>
            3. Click Download Config<br>
            4. Import the config file into your VPN client app<br>
            5. Connect to the VPN server<br>
            <br>
            <strong>💡 Current available client:</strong> <code>admin</code> (only one client exists currently)
        </div>
        
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
            <strong>Quick Links:</strong><br>
            <a href="/list" style="color: #667eea; text-decoration: none; margin-right: 15px;">📋 View All Available Clients (JSON)</a>
            <a href="/clients" style="color: #667eea; text-decoration: none;">📥 View Clients with Download Links</a>
        </div>
        
        <div style="margin-top: 15px; padding: 15px; background: #f0f7ff; border-radius: 8px; border-left: 4px solid #667eea;">
            <strong>💡 Note:</strong> If you don't know your client name, check <a href="/list" style="color: #667eea; font-weight: bold;">/list</a> to see all available clients. 
            Old clients have been removed - only current clients are shown.
        </div>
    </div>
    
    <script>
        function selectConfig(type) {
            // Update radio button
            document.getElementById('config-' + type).checked = true;
            
            // Update visual selection
            document.querySelectorAll('.config-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            event.currentTarget.classList.add('selected');
        }
        
        // Auto-select based on device type
        window.addEventListener('DOMContentLoaded', function() {
            const userAgent = navigator.userAgent.toLowerCase();
            const isMobile = /iphone|ipad|ipod|android|mobile|tablet/.test(userAgent);
            
            if (isMobile) {
                selectConfig('openvpn');
                document.getElementById('config-openvpn').checked = true;
            } else {
                // Default to both for desktop users so they have options
                selectConfig('both');
                document.getElementById('config-both').checked = true;
            }
        });
        
        function downloadConfig(event) {
            event.preventDefault();
            const clientName = document.getElementById('clientName').value.trim();
            const configType = document.querySelector('input[name="configType"]:checked').value;
            const messageDiv = document.getElementById('message');
            const downloadBtn = document.getElementById('downloadBtn');
            
            if (!clientName) {
                messageDiv.innerHTML = '<div class="error">Please enter a client name</div>';
                return;
            }
            
            // Disable button during download
            downloadBtn.disabled = true;
            downloadBtn.textContent = '⏳ Downloading...';
            messageDiv.innerHTML = '<div class="info">Downloading... Please wait.</div>';
            
            if (configType === 'both') {
                // Download all configs sequentially
                downloadAllConfigs(clientName, messageDiv, downloadBtn);
            } else {
                // Download single config
                downloadSingleConfig(clientName, configType, messageDiv, downloadBtn);
            }
        }
        
        function downloadSingleConfig(clientName, configType, messageDiv, downloadBtn) {
            const extensions = {
                'openvpn': '.ovpn',
                'phazevpn': '.phazevpn',
                'wireguard': '.conf'
            };
            const extension = extensions[configType] || '.ovpn';
            const downloadUrl = '/download?name=' + encodeURIComponent(clientName) + '&type=' + configType;
            
            // Use fetch to download and create blob (most reliable method)
            fetch(downloadUrl)
                .then(response => {
                    if (!response.ok) {
                        if (response.status === 404) {
                            throw new Error('Client not found');
                        }
                        throw new Error('Download failed: ' + response.status);
                    }
                    return response.blob();
                })
                .then(blob => {
                    // Create download link from blob
                    const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
                    link.href = url;
            link.download = clientName + extension;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            
                    // Clean up
            setTimeout(() => {
                        if (document.body.contains(link)) {
                            document.body.removeChild(link);
                        }
                        window.URL.revokeObjectURL(url);
                    }, 1000);
                    
                    messageDiv.innerHTML = '<div class="info" style="color: #4caf50;">✅ Download started! Check your downloads folder.</div>';
                        downloadBtn.disabled = false;
                        downloadBtn.textContent = '📥 Download Config';
                    })
                .catch(error => {
                    console.error('Download error:', error);
                    
                    // Fallback: Direct link download
                    const link = document.createElement('a');
                    link.href = downloadUrl;
                    link.download = clientName + extension;
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    
                    setTimeout(() => {
                        if (document.body.contains(link)) {
                            document.body.removeChild(link);
                        }
                    }, 1000);
                    
                    if (error.message === 'Client not found') {
                        messageDiv.innerHTML = '<div class="error">❌ Client &quot;' + clientName + '&quot; not found. <a href="/list" style="color: #667eea;">Check available clients</a> or <a href="' + downloadUrl + '" download="' + clientName + extension + '" style="color: #667eea; font-weight: bold;">try direct download</a></div>';
                    } else {
                        messageDiv.innerHTML = '<div class="info" style="color: #4caf50;">✅ Download initiated! If it didn\'t work, <a href="' + downloadUrl + '" download="' + clientName + extension + '" style="color: #667eea; font-weight: bold;">CLICK HERE TO DOWNLOAD</a></div>';
                    }
                        downloadBtn.disabled = false;
                        downloadBtn.textContent = '📥 Download Config';
                    });
        }
        
        function downloadAllConfigs(clientName, messageDiv, downloadBtn) {
            // Download all three configs: OpenVPN, PhazeVPN, and WireGuard
            const openvpnUrl = '/download?name=' + encodeURIComponent(clientName) + '&type=openvpn';
            const phazevpnUrl = '/download?name=' + encodeURIComponent(clientName) + '&type=phazevpn';
            const wireguardUrl = '/download?name=' + encodeURIComponent(clientName) + '&type=wireguard';
            
            // Download OpenVPN
            const link1 = document.createElement('a');
            link1.href = openvpnUrl;
            link1.download = clientName + '.ovpn';
            link1.style.display = 'none';
            document.body.appendChild(link1);
            link1.click();
            document.body.removeChild(link1);
            
            // Download PhazeVPN after a short delay
            setTimeout(() => {
                const link2 = document.createElement('a');
                link2.href = phazevpnUrl;
                link2.download = clientName + '.phazevpn';
                link2.style.display = 'none';
                document.body.appendChild(link2);
                link2.click();
                document.body.removeChild(link2);
                
                // Check both downloads
                setTimeout(() => {
                    Promise.all([
                        fetch(openvpnUrl).then(r => r.ok),
                        fetch(phazevpnUrl).then(r => r.ok)
                    ]).then(([openvpnOk, phazevpnOk]) => {
                        if (openvpnOk && phazevpnOk) {
                            messageDiv.innerHTML = '<div class="info" style="color: #4caf50;">✅ Both configurations downloaded! If downloads did not start, <a href="' + openvpnUrl + '" style="color: #667eea;">download OpenVPN</a> or <a href="' + phazevpnUrl + '" style="color: #667eea;">download PhazeVPN</a> directly.</div>';
                        } else if (openvpnOk) {
                            messageDiv.innerHTML = '<div class="info" style="color: #4caf50;">✅ OpenVPN config downloaded! <a href="' + phazevpnUrl + '" style="color: #667eea;">Click here to download PhazeVPN config</a></div>';
                        } else if (phazevpnOk) {
                            messageDiv.innerHTML = '<div class="info" style="color: #4caf50;">✅ PhazeVPN config downloaded! <a href="' + openvpnUrl + '" style="color: #667eea;">Click here to download OpenVPN config</a></div>';
                        } else {
                            messageDiv.innerHTML = '<div class="error">❌ Client &quot;' + clientName + '&quot; not found. Please check the name and try again.</div>';
                        }
                        downloadBtn.disabled = false;
                        downloadBtn.textContent = '📥 Download Config';
                    }).catch(() => {
                        messageDiv.innerHTML = '<div class="info">✅ Downloads initiated! If they did not start, <a href="' + openvpnUrl + '" style="color: #667eea;">download OpenVPN</a> or <a href="' + phazevpnUrl + '" style="color: #667eea;">download PhazeVPN</a> directly.</div>';
                        downloadBtn.disabled = false;
                        downloadBtn.textContent = '📥 Download Config';
                    });
                }, 2000);
            }, 500);
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def load_users(self):
        """Load users from users.json (shared with web portal)"""
        if not USERS_FILE.exists():
            return {}
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load users: {e}")
            return {}
    
    def verify_client_access(self, client_name, token=None, username=None):
        """Verify that the user has access to download this client config"""
        # Option 1: Token-based authentication (if token provided)
        if token:
            # Check token against a token file or database
            token_file = VPN_DIR / 'download-tokens.json'
            if token_file.exists():
                try:
                    with open(token_file, 'r') as f:
                        tokens = json.load(f)
                    if token in tokens:
                        token_data = tokens[token]
                        allowed_clients = token_data.get('clients', [])
                        # Check if token is expired
                        if 'expires' in token_data:
                            from datetime import datetime
                            if datetime.now().isoformat() > token_data['expires']:
                                return False, "Token has expired"
                        if client_name in allowed_clients:
                            return True, None
                        return False, f"Token does not have access to client '{client_name}'"
                except Exception as e:
                    print(f"Warning: Could not verify token: {e}")
        
        # Option 2: Username-based authentication (check users.json)
        if username:
            users = self.load_users()
            if username in users:
                user = users[username]
                user_clients = user.get('clients', [])
                if client_name in user_clients:
                    # Verify client file actually exists
                    config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
                    wireguard_dir = Path(__file__).parent / 'wireguard' / 'clients'
                    wg_config = wireguard_dir / f'{client_name}.conf' if wireguard_dir.exists() else None
                    
                    if config_file.exists() or (wg_config and wg_config.exists()):
                        return True, None
                    return False, f"Client '{client_name}' file not found"
                return False, f"You do not have access to client '{client_name}'. You can only download your own clients."
            return False, f"User '{username}' not found"
        
        # Option 3: If authentication is required but no token/username provided
        if REQUIRE_AUTHENTICATION:
            return False, "Authentication required. Please log in to the web portal or provide a valid token."
        
        # Option 4: Open access (authentication disabled) - just check if file exists
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
        if config_file.exists():
            return True, None
        
        # Check WireGuard clients
        wireguard_dir = Path(__file__).parent / 'wireguard' / 'clients'
        if wireguard_dir.exists():
            wg_config = wireguard_dir / f'{client_name}.conf'
            if wg_config.exists():
                return True, None
        
        return False, f"Client '{client_name}' not found or access denied"
    
    def handle_download(self, parsed_path):
        """Handle config file download - Auto-detect device type"""
        query_params = parse_qs(parsed_path.query)
        client_name = query_params.get('name', [None])[0]
        config_type = query_params.get('type', [None])[0]  # phazevpn, openvpn, or auto
        token = query_params.get('token', [None])[0]  # Optional authentication token
        username = query_params.get('username', [None])[0]  # Optional username for auth
        
        # Also check for username in cookies (if coming from web portal)
        username_from_cookie = None
        try:
            cookie_header = self.headers.get('Cookie', '')
            if 'username=' in cookie_header:
                for cookie in cookie_header.split(';'):
                    if 'username=' in cookie:
                        username_from_cookie = cookie.split('username=')[1].strip().split(';')[0]
                        break
        except:
            pass
        
        # Use cookie username if no username in query
        if not username and username_from_cookie:
            username = username_from_cookie
        
        if not client_name:
            self.send_error(400, "Client name required")
            return
        
        # Security: Remove any path traversal attempts
        client_name = os.path.basename(client_name)
        
        # Strip file extensions if user entered them (e.g., "admin.phazevpn" -> "admin")
        # This prevents confusion when users see the file extension in the filename
        if '.' in client_name:
            # Remove common extensions
            extensions_to_strip = ['.ovpn', '.phazevpn', '.conf', '.OVPN', '.PHAZEVPN', '.CONF']
            for ext in extensions_to_strip:
                if client_name.lower().endswith(ext.lower()):
                    client_name = client_name[:-len(ext)]
                    print(f"Stripped extension from client name, using: {client_name}")
                    break
        
        # Verify access (authentication check) - always check, but REQUIRE_AUTHENTICATION controls strictness
        has_access, error_msg = self.verify_client_access(client_name, token, username)
        if not has_access and REQUIRE_AUTHENTICATION:
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Access Denied - PhazeVPN</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }}
                        .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                        h1 {{ color: #f44336; }}
                        .error {{ color: #f44336; background: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                        a {{ color: #667eea; text-decoration: none; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>❌ Access Denied</h1>
                        <div class="error">
                            <p><strong>{error_msg or "You do not have permission to download this client config."}</strong></p>
                            <p>Please log in to the web portal and download from there, or use a valid authentication token.</p>
                        </div>
                        <p><a href="/">← Back to Download Page</a></p>
                    </div>
                </body>
                </html>
                """
                self.send_response(403)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(error_html.encode())
                return
        
        # Auto-detect device type if not specified
        if not config_type or config_type == 'auto':
            user_agent = self.headers.get('User-Agent', '').lower()
            # Check if mobile device
            is_mobile = any(mobile in user_agent for mobile in [
                'iphone', 'ipad', 'ipod', 'android', 'mobile', 'tablet'
            ])
            config_type = 'openvpn' if is_mobile else 'phazevpn'
        
        # Get server info
        server_host = os.environ.get('PHAZEVPN_SERVER_HOST', 'phazevpn.com')
        server_port = int(os.environ.get('PHAZEVPN_SERVER_PORT', '51821'))
        wireguard_port = int(os.environ.get('WIREGUARD_SERVER_PORT', '51820'))
        
        if config_type == 'phazevpn':
            # Generate PhazeVPN Protocol config (for desktop)
            # Try to load PhazeVPN module (lazy load)
            phazevpn_func = load_phazevpn_module()
                
            if phazevpn_func:
                try:
                # Try to get or create user in PhazeVPN client manager
                password = None
                try:
                    phazevpn_protocol_path = Path(__file__).parent / 'phazevpn-protocol'
                    sys.path.insert(0, str(phazevpn_protocol_path))
                    from client_manager import ClientManager
                    
                    manager = ClientManager()
                    if client_name in manager.users:
                        config_path = manager.client_configs_dir / f"{client_name}.phazevpn"
                        if config_path.exists():
                            try:
                                with open(config_path, 'r') as f:
                                    content = f.read()
                                    try:
                                        existing_config = json.loads(content)
                                        password = existing_config.get('authentication', {}).get('password')
                                    except json.JSONDecodeError:
                                        import configparser
                                        config_parser = configparser.ConfigParser()
                                        config_parser.read_string(content)
                                        if config_parser.has_section('Connection'):
                                            password = config_parser.get('Connection', 'password', fallback=None)
                            except Exception as e:
                                print(f"Warning: Could not read password from existing config: {e}")
                        
                        if not password:
                            password = manager.reset_password(client_name)
                            print(f"Generated new password for {client_name}")
                    else:
                        user_info = manager.create_user(client_name, password=None, mode='normal')
                        password = user_info.get('password')
                        print(f"Created new PhazeVPN user: {client_name}")
                    except (ImportError, Exception) as e:
                    print(f"Warning: Could not access PhazeVPN client manager: {e}")
                    import secrets
                    password = secrets.token_urlsafe(12)
                
                    # Generate PhazeVPN config
                    config_file = phazevpn_func(
                    client_name, server_host, server_port,
                    username=client_name, password=password,
                    output_dir=CLIENT_CONFIGS_DIR
                )
                    # Use octet-stream to force download instead of displaying JSON
                    content_type = 'application/octet-stream'
                filename = f'{client_name}.phazevpn'
            except Exception as e:
                # Fallback to OpenVPN if PhazeVPN Protocol fails
                print(f"Warning: PhazeVPN Protocol config generation failed: {e}")
                traceback.print_exc()
                config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
                content_type = 'application/x-openvpn-profile'
                filename = f'{client_name}.ovpn'
            else:
                # PhazeVPN module not available - fallback to OpenVPN
                print(f"Warning: PhazeVPN protocol not available, using OpenVPN config")
                config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
                content_type = 'application/x-openvpn-profile'
                filename = f'{client_name}.ovpn'
        elif config_type == 'wireguard':
            # WireGuard config (for gaming/streaming - fastest)
            wireguard_dir = Path(__file__).parent / 'wireguard' / 'clients'
            config_file = wireguard_dir / f'{client_name}.conf'
            
            # If WireGuard config doesn't exist, try to generate it
            if not config_file.exists():
                # Try to run WireGuard client generation script
                wg_add_client = Path(__file__).parent / 'wireguard' / 'add-client.sh'
                if wg_add_client.exists():
                    try:
                        import subprocess
                        result = subprocess.run(
                            [str(wg_add_client), client_name],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            print(f"Generated WireGuard config for {client_name}")
                        else:
                            print(f"Warning: WireGuard client generation failed: {result.stderr}")
                    except Exception as e:
                        print(f"Warning: Could not generate WireGuard config: {e}")
            
            content_type = 'text/plain'
            filename = f'{client_name}.conf'
        else:
            # OpenVPN config (for mobile devices)
            config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
            content_type = 'application/x-openvpn-profile'
            filename = f'{client_name}.ovpn'
        
        # Ensure we have a Path object
        if isinstance(config_file, str):
            config_file = Path(config_file)
        
        # Resolve absolute path (fixes symlink and relative path issues on Linux)
        config_file = config_file.resolve()
        
        # Try alternative paths if file doesn't exist (Linux case-sensitivity, etc.)
        if not config_file.exists():
            # Try case variations
            alt_paths = [
                CLIENT_CONFIGS_DIR / f'{client_name}.ovpn',
                CLIENT_CONFIGS_DIR / f'{client_name.lower()}.ovpn',
                CLIENT_CONFIGS_DIR / f'{client_name.upper()}.ovpn',
                CLIENT_CONFIGS_DIR / f'{client_name}.OVPN',
            ]
            
            for alt_path in alt_paths:
                if alt_path.exists():
                    config_file = alt_path.resolve()
                    content_type = 'application/x-openvpn-profile'
                    filename = f'{client_name}.ovpn'
                    break
        
        # Verify file exists and is readable
        if not config_file.exists():
            # Get actual available clients from file system
            available_clients = []
            if CLIENT_CONFIGS_DIR.exists():
                # Check for all config types
                available_clients = []
                for ext in ['.ovpn', '.phazevpn', '.conf']:
                    for f in CLIENT_CONFIGS_DIR.glob(f'*{ext}'):
                        name = f.stem
                        if name not in available_clients:
                            available_clients.append(name)
                available_clients.sort()
            
            # Also check WireGuard clients
            wireguard_dir = Path(__file__).parent / 'wireguard' / 'clients'
            if wireguard_dir.exists():
                for f in wireguard_dir.glob('*.conf'):
                    name = f.stem
                    if name not in available_clients:
                        available_clients.append(name)
            
            available_clients.sort()
            
            if available_clients:
                clients_list = '<br>'.join([f'  • {c}' for c in available_clients[:20]])
                if len(available_clients) > 20:
                    clients_list += f'<br>  ... and {len(available_clients) - 20} more'
                clients_html = f'<p><strong>Available clients ({len(available_clients)}):</strong><br>{clients_list}</p>'
            else:
                clients_html = '<p><strong>No clients found.</strong> Please contact your administrator to create a client config.</p>'
            
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Config Not Found - PhazeVPN</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }}
                    .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                    h1 {{ color: #f44336; }}
                    .error {{ color: #f44336; background: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    a {{ color: #667eea; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Config Not Found</h1>
                    <div class="error">
                        <p><strong>Client '{client_name}' not found.</strong></p>
                        <p>Please check the client name and try again.</p>
                    </div>
                    <div class="info">
                        {clients_html}
                        <p style="margin-top: 15px;">
                            <a href="/">← Back to Download Page</a> | 
                            <a href="/list">View All Clients (JSON)</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(error_html.encode())
            return
        
        # Send the file with correct content type and filename
        try:
            # Verify file exists and is readable (double-check after path resolution)
            if not config_file.exists():
                self.send_error(404, f"Config file not found: {config_file}")
                return
            
            # Check permissions (Linux-specific)
            if not os.access(config_file, os.R_OK):
                # Try to fix permissions (if we have write access to the directory)
                try:
                    import stat
                    os.chmod(config_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                    print(f"Fixed permissions for {config_file}")
                except Exception as e:
                    print(f"Warning: Could not fix permissions: {e}")
                    self.send_error(403, f"Permission denied reading: {config_file}")
                    return
            
            # Read file content
        try:
            with open(config_file, 'rb') as f:
                content = f.read()
            except PermissionError:
                self.send_error(403, f"Permission denied reading: {config_file}")
                return
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
                return
            
            if not content:
                self.send_error(500, "Config file is empty")
                return
            
            # Validate content is not corrupted (basic check)
            if len(content) < 100:  # Config files should be at least 100 bytes
                self.send_error(500, "Config file appears to be corrupted (too small)")
                return
            
            self.send_response(200)
            
            # Force download for all config types - browsers try to display JSON/XML
            # Use application/octet-stream for PhazeVPN JSON to force download
            if filename.endswith('.phazevpn') and content_type == 'application/json':
                content_type = 'application/octet-stream'
            
            self.send_header('Content-type', content_type)
            
            # CRITICAL: Use attachment to force download, not inline display
            # Escape filename properly for Content-Disposition header
            import urllib.parse
            safe_filename = urllib.parse.quote(filename)
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"; filename*=UTF-8\'\'{safe_filename}')
            
            # Additional headers to force download
            self.send_header('Content-Length', str(len(content)))
            self.send_header('X-Content-Type-Options', 'nosniff')  # Prevent MIME sniffing
            
            # Add CORS headers to allow downloads from any origin
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            # Cache control to prevent caching issues
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            
            self.end_headers()
            self.wfile.write(content)
            self.wfile.flush()  # Ensure content is sent immediately
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Successfully sent download: {client_name} ({config_type}) - {len(content)} bytes")
            
            # Log successful download
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Downloaded: {client_name} ({config_type})")
        except PermissionError as e:
            self.send_error(403, f"Permission denied: {e}")
            print(f"ERROR: Permission denied reading {config_file}: {e}")
        except FileNotFoundError as e:
            self.send_error(404, f"File not found: {e}")
            print(f"ERROR: File not found {config_file}: {e}")
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")
            print(f"ERROR: Failed to read {config_file}: {e}")
            traceback.print_exc()
    
    def list_configs(self):
        """List available configs (for admin/debugging) - Shows ALL actual clients"""
        configs = []
        config_details = []
        
        # Check OpenVPN configs
        if CLIENT_CONFIGS_DIR.exists():
            for f in CLIENT_CONFIGS_DIR.glob('*.ovpn'):
                name = f.stem
                if name not in configs:
                    configs.append(name)
                    config_details.append({
                        'name': name,
                        'type': 'openvpn',
                        'file': f.name,
                        'exists': True
                    })
        
        # Check PhazeVPN configs
        if CLIENT_CONFIGS_DIR.exists():
            for f in CLIENT_CONFIGS_DIR.glob('*.phazevpn'):
                name = f.stem
                if name not in configs:
                    configs.append(name)
                # Add to details if not already there
                existing = next((c for c in config_details if c['name'] == name), None)
                if existing:
                    existing['phazevpn_exists'] = True
                else:
                    config_details.append({
                        'name': name,
                        'type': 'phazevpn',
                        'file': f.name,
                        'exists': True
                    })
        
        # Check WireGuard configs
        wireguard_dir = Path(__file__).parent / 'wireguard' / 'clients'
        if wireguard_dir.exists():
            for f in wireguard_dir.glob('*.conf'):
                name = f.stem
                if name not in configs:
                    configs.append(name)
                # Add to details if not already there
                existing = next((c for c in config_details if c['name'] == name), None)
                if existing:
                    existing['wireguard_exists'] = True
                else:
                    config_details.append({
                        'name': name,
                        'type': 'wireguard',
                        'file': f.name,
                        'exists': True
                    })
        
        response = {
            'status': 'ok',
            'clients': sorted(configs),
            'count': len(configs),
            'details': sorted(config_details, key=lambda x: x['name'])
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def serve_clients_page(self):
        """Serve a page listing all available clients with download links - Shows ACTUAL clients only"""
        configs = []
        config_details = {}
        
        # Check OpenVPN configs
        if CLIENT_CONFIGS_DIR.exists():
            for f in CLIENT_CONFIGS_DIR.glob('*.ovpn'):
                name = f.stem
                if name not in configs:
                    configs.append(name)
                if name not in config_details:
                    config_details[name] = {'openvpn': True, 'phazevpn': False, 'wireguard': False}
                else:
                    config_details[name]['openvpn'] = True
        
        # Check PhazeVPN configs
        if CLIENT_CONFIGS_DIR.exists():
            for f in CLIENT_CONFIGS_DIR.glob('*.phazevpn'):
                name = f.stem
                if name not in configs:
                    configs.append(name)
                if name not in config_details:
                    config_details[name] = {'openvpn': False, 'phazevpn': True, 'wireguard': False}
                else:
                    config_details[name]['phazevpn'] = True
        
        # Check WireGuard configs
        wireguard_dir = Path(__file__).parent / 'wireguard' / 'clients'
        if wireguard_dir.exists():
            for f in wireguard_dir.glob('*.conf'):
                name = f.stem
                if name not in configs:
                    configs.append(name)
                if name not in config_details:
                    config_details[name] = {'openvpn': False, 'phazevpn': False, 'wireguard': True}
                else:
                    config_details[name]['wireguard'] = True
        
        # Sort configs
        configs = sorted(configs)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Available VPN Clients</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .client-list {{
            list-style: none;
            padding: 0;
        }}
        .client-item {{
            padding: 15px;
            margin: 10px 0;
            background: #f5f5f5;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .client-name {{
            font-weight: bold;
            color: #333;
        }}
        .download-btn {{
            background: #667eea;
            color: white;
            padding: 8px 20px;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
        }}
        .download-btn:hover {{
            background: #5568d3;
        }}
        .back-link {{
            display: block;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Available VPN Clients ({len(configs)})</h1>
        <p style="color: #666; margin-bottom: 20px;">These are the current active clients. Old clients have been removed.</p>
        <p>Click a client name to download their configuration:</p>
        <ul class="client-list">
"""
        if not configs:
            html += """            <li class="client-item">
                <span class="client-name" style="color: #999;">No clients found. Please contact your administrator.</span>
            </li>
"""
        else:
        for client in configs:
                details = config_details.get(client, {})
                types_available = []
                if details.get('openvpn'):
                    types_available.append('OpenVPN')
                if details.get('phazevpn'):
                    types_available.append('PhazeVPN')
                if details.get('wireguard'):
                    types_available.append('WireGuard')
                
                types_str = f" ({', '.join(types_available)})" if types_available else ""
                
            html += f"""            <li class="client-item">
                <div>
                <span class="client-name">{client}</span>
                    <span style="color: #666; font-size: 0.9em; margin-left: 10px;">{types_str}</span>
                </div>
                <a href="/download?name={client}&type=openvpn" class="download-btn">📥 Download</a>
            </li>
"""
        html += """        </ul>
        <a href="/" class="back-link">← Back to main page</a>
    </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Log requests for debugging"""
        try:
            print(f"[{self.log_date_time_string()}] {format % args}")
        except:
            pass  # Don't crash on logging errors
    
    def handle_one_request(self):
        """Override to add error handling"""
        try:
            super().handle_one_request()
        except Exception as e:
            print(f"Error handling request: {e}")
            traceback.print_exc()
            try:
                self.send_error(500, "Internal Server Error")
            except:
                pass

def get_server_ip():
    """Get the server's IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'YOUR_SERVER_IP'

def main():
    # Kill any old instances first (in case port is in use)
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'client-download-server.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            current_pid = os.getpid()
            for pid in pids:
                if pid and int(pid) != current_pid:
                    try:
                        os.kill(int(pid), 15)  # SIGTERM
                        print(f"Killed old process: {pid}")
                        time.sleep(1)
                    except:
                        pass
    except:
        pass
    
    # Ensure client-configs directory exists
    CLIENT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check permissions
    if not os.access(CLIENT_CONFIGS_DIR, os.R_OK):
        print(f"ERROR: Cannot read from {CLIENT_CONFIGS_DIR}")
        print(f"   Run: sudo chmod 755 {CLIENT_CONFIGS_DIR}")
        sys.exit(1)
    
    server_ip = get_server_ip()
    
    print("=" * 70)
    print("PhazeVPN Client Download Server")
    print("=" * 70)
    print(f"\n📁 Config directory: {CLIENT_CONFIGS_DIR}")
    print(f"   Exists: {CLIENT_CONFIGS_DIR.exists()}")
    print(f"   Readable: {os.access(CLIENT_CONFIGS_DIR, os.R_OK) if CLIENT_CONFIGS_DIR.exists() else False}")
    
    # List available configs
    if CLIENT_CONFIGS_DIR.exists():
        configs = list(CLIENT_CONFIGS_DIR.glob('*.ovpn'))
        print(f"   Available configs: {len(configs)}")
        if configs:
            print(f"   Sample: {', '.join([f.stem for f in configs[:5]])}")
    
    print(f"\n🌐 Server running at: http://{server_ip}:{PORT}")
    print(f"📥 Clients can download configs at: http://{server_ip}:{PORT}")
    print(f"\n📋 Share this URL with your clients!")
    print(f"\n⚠️  Note: Make sure port {PORT} is open in your firewall")
    print(f"   Run: sudo ufw allow {PORT}/tcp")
    print(f"\n💡 Debug: Visit http://{server_ip}:{PORT}/list to see available configs")
    print(f"\nPress Ctrl+C to stop the server")
    print("=" * 70)
    
    # Create server with better error handling
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            server = HTTPServer(('0.0.0.0', PORT), ConfigDownloadHandler)
            print(f"\n✅ Server started successfully on port {PORT}")
            server.serve_forever()
            break
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"\n❌ Port {PORT} is already in use")
                print("   Another instance might be running")
                print("   Kill it with: pkill -f client-download-server.py")
                break
            else:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"\n⚠️  Error starting server: {e}")
                    print(f"   Retrying in 5 seconds... ({retry_count}/{max_retries})")
                    time.sleep(5)
                else:
                    print(f"\n❌ Failed to start server after {max_retries} attempts")
                    raise
        except KeyboardInterrupt:
            print("\n\nServer stopped by user.")
            try:
                server.shutdown()
            except:
                pass
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            retry_count += 1
            if retry_count < max_retries:
                print(f"   Retrying in 5 seconds... ({retry_count}/{max_retries})")
                time.sleep(5)
            else:
                raise

if __name__ == '__main__':
    main()

