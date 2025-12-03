#!/usr/bin/env python3
"""
Local config generator for GUI
Generates OpenVPN, WireGuard, and PhazeVPN configs locally
"""
import subprocess
import os
from pathlib import Path
import hashlib

# Default paths - try multiple locations
BASE_DIR = None
possible_paths = [
    Path('/opt/phaze-vpn'),
    Path(__file__).parent,
    Path.home() / '.phazevpn',
]

for path in possible_paths:
    if path.exists() and (path / 'certs').exists():
        BASE_DIR = path
        break

if not BASE_DIR:
    # Use /opt/phaze-vpn as default (will create if needed)
    BASE_DIR = Path('/opt/phaze-vpn')

CLIENT_CONFIGS_DIR = BASE_DIR / 'client-configs'
CERTS_DIR = BASE_DIR / 'certs'
WG_DIR = BASE_DIR / 'wireguard'
PHAZEVPN_DIR = BASE_DIR / 'phazevpn-protocol-go'

# Ensure directories exist
CLIENT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

def generate_openvpn_config(client_name, server_host='phazevpn.com', server_port=1194):
    """Generate OpenVPN config file"""
    try:
        ca_crt = CERTS_DIR / 'ca.crt'
        client_crt = CERTS_DIR / f'{client_name}.crt'
        client_key = CERTS_DIR / f'{client_name}.key'
        ta_key = CERTS_DIR / 'ta.key'
        
        # Check if certificates exist
        if not ca_crt.exists():
            return None, "CA certificate not found"
        
        if not client_crt.exists() or not client_key.exists():
            return None, f"Client certificates not found for {client_name}"
        
        # Read certificate files
        with open(ca_crt) as f:
            ca_content = f.read()
        
        with open(client_crt) as f:
            client_crt_content = f.read()
        
        with open(client_key) as f:
            client_key_content = f.read()
        
        # TLS auth (optional)
        tls_auth = ''
        if ta_key.exists():
            with open(ta_key) as f:
                ta_content = f.read()
            tls_auth = f'''<tls-auth>
{ta_content}</tls-auth>
key-direction 1
'''
        
        # Generate config
        config_content = f'''# OpenVPN Client Configuration for {client_name}
# Generated automatically

client
dev tun
proto udp
remote {server_host} {server_port}
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA512
verb 3

<ca>
{ca_content}</ca>

<cert>
{client_crt_content}</cert>

<key>
{client_key_content}</key>
{tls_auth}
# DNS and routing
redirect-gateway def1
dhcp-option DNS 1.1.1.1
dhcp-option DNS 1.0.0.1
'''
        
        # Save config
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
        config_file.write_text(config_content)
        config_file.chmod(0o600)
        
        return str(config_file), None
        
    except Exception as e:
        return None, str(e)

def generate_wireguard_config(client_name, server_host='phazevpn.com', server_port=51820):
    """Generate WireGuard config file"""
    try:
        # Check if wg command exists
        try:
            subprocess.run(['wg', '--version'], capture_output=True, check=True)
        except:
            return None, "WireGuard tools not installed"
        
        # Generate client keys
        client_private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
        client_public_key = subprocess.check_output(
            ['wg', 'pubkey'], 
            input=client_private_key.encode()
        ).decode().strip()
        
        # Get server public key (try multiple locations)
        server_key = None
        server_key_paths = [
            '/etc/phazevpn/wireguard/server_public.key',
            BASE_DIR / 'wireguard' / 'server_public.key',
            BASE_DIR / 'phazevpn-protocol-go' / 'server_public.key',
        ]
        
        for key_path in server_key_paths:
            key_path = Path(key_path)
            if key_path.exists():
                server_key = key_path.read_text().strip()
                break
        
        if not server_key:
            # Use placeholder - will need to be updated
            server_key = "SERVER_PUBLIC_KEY_PLACEHOLDER"
        
        # Assign client IP (deterministic based on name)
        ip_hash = int(hashlib.md5(client_name.encode()).hexdigest(), 16)
        client_ip = f"10.8.0.{(ip_hash % 250) + 2}/24"
        
        # Generate config
        config_content = f'''# WireGuard Client Configuration for {client_name}
# Generated automatically

[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = {server_key}
Endpoint = {server_host}:{server_port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
'''
        
        # Save config
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.conf'
        config_file.write_text(config_content)
        config_file.chmod(0o600)
        
        # Also save private key separately (for server to add peer)
        private_key_file = CLIENT_CONFIGS_DIR / f'{client_name}_wg_private.key'
        private_key_file.write_text(client_private_key)
        private_key_file.chmod(0o600)
        
        return str(config_file), None
        
    except Exception as e:
        return None, str(e)

def generate_phazevpn_config(client_name, server_host='phazevpn.com', server_port=51821):
    """Generate PhazeVPN config file"""
    try:
        # Try using the Go script if available
        go_generator = PHAZEVPN_DIR / 'scripts' / 'generate-phazevpn-client-config.py'
        
        if go_generator.exists():
            try:
                result = subprocess.run(
                    ['python3', str(go_generator), client_name, server_host, str(server_port)],
                    cwd=str(go_generator.parent),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    # Check if config was created
                    config_file = CLIENT_CONFIGS_DIR / f'{client_name}_phazevpn.conf'
                    if config_file.exists():
                        return str(config_file), None
            except Exception as e:
                print(f"Go generator failed: {e}")
        
        # Fallback: Create simple config
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.phazevpn'
        
        # Generate client keys (simplified)
        import secrets
        client_private_key = secrets.token_urlsafe(32)
        client_public_key = secrets.token_urlsafe(32)
        
        # Get server key (placeholder if not found)
        server_key = "SERVER_PUBLIC_KEY_PLACEHOLDER"
        server_key_paths = [
            BASE_DIR / 'phazevpn-protocol-go' / 'server_public.key',
            '/etc/phazevpn/server_public.key',
        ]
        for key_path in server_key_paths:
            if Path(key_path).exists():
                server_key = Path(key_path).read_text().strip()
                break
        
        # Assign client IP
        ip_hash = int(hashlib.md5(client_name.encode()).hexdigest(), 16)
        client_ip = f"10.9.0.{(ip_hash % 250) + 2}"
        
        config_content = f'''[PhazeVPN]
Server = {server_host}:{server_port}
ServerPublicKey = {server_key}
ClientPrivateKey = {client_private_key}
ClientPublicKey = {client_public_key}
VPNNetwork = 10.9.0.0/24
ClientIP = {client_ip}

# PhazeVPN Protocol Configuration
# Generated automatically - keep this file secure!
# Do not share your ClientPrivateKey with anyone.
'''
        
        config_file.write_text(config_content)
        config_file.chmod(0o600)
        
        return str(config_file), None
        
    except Exception as e:
        return None, str(e)

def generate_all_configs(client_name, server_host='phazevpn.com'):
    """Generate all three protocol configs"""
    results = {
        'openvpn': {'success': False, 'file': None, 'error': None},
        'wireguard': {'success': False, 'file': None, 'error': None},
        'phazevpn': {'success': False, 'file': None, 'error': None},
    }
    
    # Generate OpenVPN
    file, error = generate_openvpn_config(client_name, server_host, 1194)
    if file:
        results['openvpn'] = {'success': True, 'file': file, 'error': None}
    else:
        results['openvpn'] = {'success': False, 'file': None, 'error': error}
    
    # Generate WireGuard
    file, error = generate_wireguard_config(client_name, server_host, 51820)
    if file:
        results['wireguard'] = {'success': True, 'file': file, 'error': None}
    else:
        results['wireguard'] = {'success': False, 'file': None, 'error': error}
    
    # Generate PhazeVPN
    file, error = generate_phazevpn_config(client_name, server_host, 51821)
    if file:
        results['phazevpn'] = {'success': True, 'file': file, 'error': None}
    else:
        results['phazevpn'] = {'success': False, 'file': None, 'error': error}
    
    return results

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 gui-config-generator.py <client-name> [protocol]")
        print("Protocols: openvpn, wireguard, phazevpn, all (default: all)")
        sys.exit(1)
    
    client_name = sys.argv[1]
    protocol = sys.argv[2] if len(sys.argv) > 2 else 'all'
    
    if protocol == 'all':
        results = generate_all_configs(client_name)
        for proto, result in results.items():
            if result['success']:
                print(f"✅ {proto.upper()}: {result['file']}")
            else:
                print(f"❌ {proto.upper()}: {result['error']}")
    elif protocol == 'openvpn':
        file, error = generate_openvpn_config(client_name)
        if file:
            print(f"✅ OpenVPN: {file}")
        else:
            print(f"❌ OpenVPN: {error}")
    elif protocol == 'wireguard':
        file, error = generate_wireguard_config(client_name)
        if file:
            print(f"✅ WireGuard: {file}")
        else:
            print(f"❌ WireGuard: {error}")
    elif protocol == 'phazevpn':
        file, error = generate_phazevpn_config(client_name)
        if file:
            print(f"✅ PhazeVPN: {file}")
        else:
            print(f"❌ PhazeVPN: {error}")
    else:
        print(f"Unknown protocol: {protocol}")

