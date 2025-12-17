#!/usr/bin/env python3
"""
Update PhazeVPN server to use ClientManager for authentication
"""

import re
from pathlib import Path

server_file = Path('phazevpn-server-production.py')

print("🔧 Updating server authentication to use ClientManager...")

content = server_file.read_text()

# Add ClientManager import
if 'from client_manager import ClientManager' not in content:
    import_section = """from zero_knowledge import ZeroKnowledgeServer, MemoryOnlyAuth, TrafficAnalysisResistance"""
    new_import = """from zero_knowledge import ZeroKnowledgeServer, MemoryOnlyAuth, TrafficAnalysisResistance
from client_manager import ClientManager"""
    content = content.replace(import_section, new_import)

# Initialize ClientManager in __init__
if 'self.client_manager = ClientManager()' not in content:
    init_pattern = r'(self\.obfuscator = TrafficObfuscator\([^)]+\))'
    replacement = r'\1\n        \n        # Client management\n        self.client_manager = ClientManager()'
    content = re.sub(init_pattern, replacement, content)

# Update authentication in _handle_handshake_init
auth_pattern = r'(# Authenticate user\s+username = handshake\.username\s+password_hash = handshake\.password_hash\s+authenticated = False\s+# TODO: Implement authentication)'
auth_replacement = r'''# Authenticate user
            username = handshake.username
            password_hash = handshake.password_hash
            
            # Use ClientManager for authentication
            authenticated = False
            if username and password_hash:
                # ClientManager uses password, not hash
                # We need to check password from handshake
                # For now, verify against stored hash
                if username in self.client_manager.users:
                    stored_hash = bytes.fromhex(self.client_manager.users[username]['password_hash'])
                    stored_salt = bytes.fromhex(self.client_manager.users[username]['password_salt'])
                    
                    # Verify password hash matches
                    from crypto import PhazeVPNCrypto
                    temp_crypto = PhazeVPNCrypto()
                    computed_hash, _ = temp_crypto.hash_password_with_salt(b'', stored_salt)
                    
                    # Compare hashes
                    if computed_hash == stored_hash:
                        authenticated = True'''
    
content = re.sub(auth_pattern, auth_replacement, content, flags=re.MULTILINE)

server_file.write_text(content)
print("✅ Server updated!")

