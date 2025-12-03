#!/usr/bin/env python3
"""
PhazeVPN Protocol - Client Manager
Create users, generate client configs, manage clients
"""

import json
import os
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

class ClientManager:
    """
    Manages clients for PhazeVPN Protocol
    Creates users, stores credentials, generates client configs
    """
    
    def __init__(self, vpn_dir='/opt/secure-vpn'):
        self.vpn_dir = Path(vpn_dir)
        # Ensure directory exists or use local directory
        try:
            if not self.vpn_dir.exists():
                # Try to create, but fall back to local if no permission
                try:
                    self.vpn_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    # Fall back to local directory
                    self.vpn_dir = Path(__file__).parent.parent
        except Exception:
            # Fall back to local directory
            self.vpn_dir = Path(__file__).parent.parent
        
        self.users_db = self.vpn_dir / 'phazevpn-users.json'
        self.client_configs_dir = self.vpn_dir / 'phazevpn-client-configs'
        
        # Try to create directory, but don't fail if no permission
        try:
            self.client_configs_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # Fall back to local directory
            self.client_configs_dir = Path(__file__).parent / 'client-configs'
            self.client_configs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing users
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Load users database"""
        if self.users_db.exists():
            try:
                with open(self.users_db, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_users(self):
        """Save users database"""
        self.users_db.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_db, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def create_user(self, username: str, password: str = None, mode: str = 'normal') -> Dict:
        """
        Create new user
        Returns user info including credentials
        """
        if username in self.users:
            raise ValueError(f"User {username} already exists")
        
        # Generate password if not provided
        if not password:
            password = secrets.token_urlsafe(16)  # 16 bytes = secure random password
        
        # Hash password (using PBKDF2)
        from crypto import PhazeVPNCrypto
        crypto = PhazeVPNCrypto()
        password_hash, salt = crypto.hash_password(password)
        
        # Store user
        self.users[username] = {
            'username': username,
            'password_hash': password_hash.hex(),
            'password_salt': salt.hex(),
            'mode': mode,  # normal, semi_ghost, full_ghost
            'created': datetime.now().isoformat(),
            'active': True,
            'last_connected': None,
            'total_connections': 0
        }
        
        self._save_users()
        
        # Generate client config
        config_file = self.generate_client_config(username, password, mode)
        
        return {
            'username': username,
            'password': password,  # Return plain password for user (only time it's shown)
            'mode': mode,
            'config_file': str(config_file),
            'created': self.users[username]['created']
        }
    
    def generate_client_config(self, username: str, password: str, mode: str = 'normal', 
                               server_ip: str = None, server_port: int = 51821) -> Path:
        """
        Generate client configuration file
        Returns path to config file
        """
        if not server_ip:
            server_ip = "15.204.11.19"  # Default VPS IP
        
        config_content = f"""# PhazeVPN Protocol Client Configuration
# Generated for: {username}
# Mode: {mode}
# Server: {server_ip}:{server_port}

[Connection]
server = {server_ip}
port = {server_port}
username = {username}
password = {password}

[Mode]
mode = {mode}

[Network]
vpn_interface = phazevpn0
vpn_network = 10.9.0.0/24

[Security]
# PhazeVPN Protocol features
# - Zero-knowledge (no logging)
# - Traffic obfuscation (DPI evasion)
# - Perfect Forward Secrecy (auto-rekey)
# - Replay protection

[Advanced]
# Mode-specific features are automatically applied
# Normal: Fast, standard privacy
# Semi Ghost: Enhanced privacy, good speed
# Full Ghost: Maximum stealth, slower
"""
        
        config_file = self.client_configs_dir / f"{username}.phazevpn"
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Also create Python script version
        script_file = self.client_configs_dir / f"{username}.py"
        script_content = f"""#!/usr/bin/env python3
\"\"\"
PhazeVPN Protocol Client - {username}
Auto-generated client script
\"\"\"

import sys
from pathlib import Path

# Add protocol directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phazevpn_client import PhazeVPNClient

def main():
    client = PhazeVPNClient(
        server_host="{server_ip}",
        server_port={server_port},
        username="{username}",
        password="{password}"
    )
    
    try:
        client.connect()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
"""
        with open(script_file, 'w') as f:
            f.write(script_content)
        script_file.chmod(0o755)  # Make executable
        
        return config_file
    
    def list_users(self) -> list:
        """List all users"""
        return [
            {
                'username': username,
                'mode': user_data.get('mode', 'normal'),
                'created': user_data.get('created'),
                'active': user_data.get('active', True),
                'total_connections': user_data.get('total_connections', 0)
            }
            for username, user_data in self.users.items()
        ]
    
    def delete_user(self, username: str):
        """Delete user"""
        if username in self.users:
            del self.users[username]
            self._save_users()
            
            # Delete client configs
            config_file = self.client_configs_dir / f"{username}.phazevpn"
            script_file = self.client_configs_dir / f"{username}.py"
            if config_file.exists():
                config_file.unlink()
            if script_file.exists():
                script_file.unlink()
            
            return True
        return False
    
    def update_user_mode(self, username: str, mode: str):
        """Update user's VPN mode"""
        if username not in self.users:
            raise ValueError(f"User {username} not found")
        
        valid_modes = ['normal', 'semi_ghost', 'full_ghost']
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        
        self.users[username]['mode'] = mode
        self._save_users()
    
    def reset_password(self, username: str) -> str:
        """Reset user password and return new password"""
        if username not in self.users:
            raise ValueError(f"User {username} not found")
        
        # Generate new password
        new_password = secrets.token_urlsafe(16)
        
        # Hash new password
        from crypto import PhazeVPNCrypto
        crypto = PhazeVPNCrypto()
        password_hash, salt = crypto.hash_password(new_password)
        
        # Update user
        self.users[username]['password_hash'] = password_hash.hex()
        self.users[username]['password_salt'] = salt.hex()
        self._save_users()
        
        # Regenerate client config with new password
        self.generate_client_config(username, new_password, self.users[username].get('mode', 'normal'))
        
        return new_password
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information"""
        if username not in self.users:
            return None
        
        user_data = self.users[username].copy()
        # Don't return password hash
        user_data.pop('password_hash', None)
        user_data.pop('password_salt', None)
        return user_data
    
    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        if username not in self.users:
            return False
        
        if not self.users[username].get('active', True):
            return False
        
        # Verify password
        from crypto import PhazeVPNCrypto
        crypto = PhazeVPNCrypto()
        stored_hash = bytes.fromhex(self.users[username]['password_hash'])
        stored_salt = bytes.fromhex(self.users[username]['password_salt'])
        
        return crypto.verify_password(password, stored_hash, stored_salt)

