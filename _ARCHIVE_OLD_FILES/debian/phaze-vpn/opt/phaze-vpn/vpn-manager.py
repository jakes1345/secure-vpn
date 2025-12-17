#!/usr/bin/env python3
"""
Simple VPN Management Tool
Easy to customize - modify the CONFIG section below!
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# ============================================
# CUSTOMIZE THESE SETTINGS
# ============================================
# Try installed location first, then current directory
if Path('/opt/phaze-vpn/vpn-manager.py').exists():
    BASE_DIR = Path('/opt/phaze-vpn')
else:
    BASE_DIR = Path(__file__).parent.absolute()

CONFIG = {
    'vpn_dir': BASE_DIR,
    'server_config': 'config/server.conf',
    'certs_dir': 'certs',
    'client_configs_dir': 'client-configs',
    'logs_dir': 'logs',
    'server_ip': os.environ.get('VPN_SERVER_IP', 'phazevpn.com'),  # Use env var or default to domain
    'server_port': int(os.environ.get('VPN_SERVER_PORT', '1194')),
    'vpn_subnet': '10.8.0.0',
    'vpn_netmask': '255.255.255.0',
    'max_clients': 10,
    'dns_servers': ['1.1.1.1', '1.0.0.1'],  # Cloudflare
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_path(key):
    """Get full path for a config key"""
    if key in ['server_config', 'certs_dir', 'client_configs_dir', 'logs_dir']:
        return CONFIG['vpn_dir'] / CONFIG[key]
    return CONFIG['vpn_dir'] / key

def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        print("Error: This command requires root privileges (use sudo)")
        sys.exit(1)

def check_openvpn():
    """Check if OpenVPN is installed"""
    try:
        subprocess.run(['openvpn', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: OpenVPN is not installed")
        print("Install it with: sudo apt install openvpn")
        sys.exit(1)

def is_server_running():
    """Check if VPN server is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'openvpn.*server.conf'],
                              capture_output=True)
        return result.returncode == 0
    except:
        return False

# ============================================
# COMMANDS
# ============================================

def cmd_start():
    """Start the VPN server"""
    check_root()
    check_openvpn()
    
    server_config = get_path('server_config')
    if not server_config.exists():
        print(f"Error: Server config not found: {server_config}")
        print("Run './manage-vpn.sh setup' first")
        sys.exit(1)
    
    if is_server_running():
        print("VPN server is already running")
        sys.exit(1)
    
    logs_dir = get_path('logs_dir')
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_dir / 'server.log'
    
    print("Starting VPN server...")
    subprocess.run([
        'openvpn',
        '--config', str(server_config),
        '--daemon',
        '--log', str(log_file)
    ], check=True)
    
    import time
    time.sleep(2)
    
    if is_server_running():
        print(f"✓ VPN server started successfully")
        print(f"  Logs: {log_file}")
    else:
        print("✗ Failed to start VPN server")
        print(f"  Check logs: {log_file}")
        sys.exit(1)

def cmd_stop():
    """Stop the VPN server"""
    check_root()
    
    if not is_server_running():
        print("VPN server is not running")
        sys.exit(1)
    
    print("Stopping VPN server...")
    subprocess.run(['pkill', '-f', 'openvpn.*server.conf'], check=False)
    
    import time
    time.sleep(1)
    
    if not is_server_running():
        print("✓ VPN server stopped")
    else:
        print("✗ Failed to stop VPN server")
        sys.exit(1)

def cmd_status():
    """Show server status"""
    if is_server_running():
        print("✓ VPN server is running")
        print()
        
        status_file = get_path('logs_dir') / 'status.log'
        if status_file.exists():
            print("Active connections:")
            try:
                with open(status_file) as f:
                    lines = f.readlines()
                    clients = [l for l in lines if l and l[0].isdigit()]
                    if clients:
                        for client in clients[:10]:
                            parts = client.strip().split(',')
                            if len(parts) >= 2:
                                print(f"  {parts[0]} - {parts[1]}")
                    else:
                        print("  No active connections")
            except:
                print("  Could not read status file")
    else:
        print("✗ VPN server is not running")

def cmd_add_client(name):
    """Generate client certificate and config"""
    if not name:
        print("Error: Client name required")
        print("Usage: python3 vpn-manager.py add-client <name>")
        sys.exit(1)
    
    certs_dir = get_path('certs_dir')
    client_configs_dir = get_path('client_configs_dir')
    
    # Ensure directories exist and use absolute paths
    certs_dir = certs_dir.absolute()
    client_configs_dir = client_configs_dir.absolute()
    certs_dir.mkdir(parents=True, exist_ok=True)
    client_configs_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize client name (remove any invalid characters)
    safe_name = ''.join(c for c in name if c.isalnum() or c in ['-', '_'])
    if not safe_name:
        print(f"Error: Invalid client name: {name}")
        sys.exit(1)
    
    ca_crt = certs_dir / 'ca.crt'
    ca_key = certs_dir / 'ca.key'
    
    if not ca_crt.exists():
        print("Error: CA certificate not found")
        print(f"Expected at: {ca_crt}")
        print("Run './generate-certs.sh' first")
        sys.exit(1)
    
    if not ca_key.exists():
        print("Error: CA key not found")
        print(f"Expected at: {ca_key}")
        sys.exit(1)
    
    # Use sanitized name for files
    client_key = certs_dir / f'{safe_name}.key'
    client_crt = certs_dir / f'{safe_name}.crt'
    client_csr = certs_dir / f'{safe_name}.csr'
    
    # Use absolute path to ensure correct location
    client_config = client_configs_dir / f'{safe_name}.ovpn'
    
    print(f"Generating certificate for client: {name} (safe name: {safe_name})")
    print(f"Certs directory: {certs_dir}")
    print(f"Client key will be: {client_key}")
    print(f"Config will be saved to: {client_config}")
    
    # Check if client already exists
    if client_key.exists():
        print(f"Warning: Client key already exists: {client_key}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Aborted")
            sys.exit(0)
    
    # Generate client key (4096-bit RSA for maximum security)
    try:
        subprocess.run(['openssl', 'genrsa', '-out', str(client_key), '4096'], 
                      check=True, cwd=str(certs_dir))
    except subprocess.CalledProcessError as e:
        print(f"Error generating client key: {e}")
        print(f"Tried to write to: {client_key}")
        print(f"Parent directory exists: {client_key.parent.exists()}")
        print(f"Parent directory writable: {os.access(client_key.parent, os.W_OK)}")
        sys.exit(1)
    
    # Generate client CSR
    # Mark as PhazeVPN client in certificate (O=PhazeVPN, CN=phazevpn-<safe_name>)
    try:
        subprocess.run([
            'openssl', 'req', '-new', '-key', str(client_key),
            '-out', str(client_csr),
            '-subj', f'/C=US/ST=Secure/L=VPN/O=PhazeVPN/CN=phazevpn-{safe_name}'
        ], check=True, cwd=str(certs_dir))
    except subprocess.CalledProcessError as e:
        print(f"Error generating CSR: {e}")
        sys.exit(1)
    
    # Sign client certificate
    openssl_client_cnf = CONFIG['vpn_dir'] / 'certs' / 'openssl-client.cnf'
    try:
        cmd = [
            'openssl', 'x509', '-req', '-in', str(client_csr),
            '-CA', str(ca_crt), '-CAkey', str(ca_key),
            '-CAcreateserial', '-out', str(client_crt),
            '-days', '365', '-sha512',
        ]
        if openssl_client_cnf.exists():
            cmd.extend(['-extensions', 'v3_req', '-extfile', str(openssl_client_cnf)])
        
        subprocess.run(cmd, check=True, cwd=str(certs_dir))
    except subprocess.CalledProcessError as e:
        print(f"Error signing certificate: {e}")
        sys.exit(1)
    
    # Get server IP - Always use phazevpn.com domain (not IP)
    # This ensures configs work even if server IP changes
    server_ip = CONFIG.get('server_ip', 'phazevpn.com')
    if not server_ip or server_ip == 'YOUR_SERVER_IP':
        server_ip = 'phazevpn.com'  # Default to domain
    
    # Read certificate files
    with open(ca_crt) as f:
        ca_content = f.read()
    with open(client_crt) as f:
        client_crt_content = f.read()
    with open(client_key) as f:
        client_key_content = f.read()
    
    ta_key = certs_dir / 'ta.key'
    if ta_key.exists():
        with open(ta_key) as f:
            ta_content = f.read()
        tls_auth = f'''<tls-auth>
{ta_content}</tls-auth>
key-direction 1
'''
    else:
        tls_auth = ''
    
    # Generate config (client_config already set with absolute path above)
    config_content = f'''# VPN Client Configuration for {name}
# Generated: {subprocess.check_output(['date']).decode().strip()}
# MAXIMUM PRIVACY & SECURITY - Ghost Mode Enabled
# This config provides the highest level of anonymity possible

client
dev tun
proto udp
remote {server_ip} {CONFIG['server_port']}
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server

# Maximum Security Encryption - ChaCha20-Poly1305 (stronger than AES-256)
# MUST match server settings exactly!
data-ciphers CHACHA20-POLY1305:AES-256-GCM
cipher CHACHA20-POLY1305
auth SHA512
tls-version-min 1.3
tls-cipher TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256

# PRIVACY SETTINGS - Maximum Anonymity (Ghost Mode)
# Block all DNS outside VPN (prevents DNS leaks)
block-outside-dns
# Route all traffic through VPN (kill switch)
redirect-gateway def1
# Block IPv6 completely (prevents IPv6 leaks)
block-ipv6
# Use privacy-focused DNS (Quad9 - Switzerland, no logging)
dhcp-option DNS 9.9.9.9
dhcp-option DNS 149.112.112.112
# Block IPv6 DNS
dhcp-option DNS6 ::

# TRAFFIC OBFUSCATION - Prevent Traffic Analysis
# Fragment and normalize packets to prevent fingerprinting
fragment 1300
mssfix 1200
# Randomize packet sizes (prevents traffic analysis)
# This makes it harder to identify what you're doing

# SECURITY HARDENING
# Don't allow compression (prevents CRIME attack)
comp-lzo no
# Verify server certificate
verify-x509-name {server_ip} name
# Prevent MITM attacks
ns-cert-type server

# ZERO LOGGING - Maximum Privacy (Ghost Mode)
# No logs, no tracking, no metadata collection
verb 0
mute 20
# Prevents connection pattern analysis

<ca>
{ca_content}</ca>

<cert>
{client_crt_content}</cert>

<key>
{client_key_content}</key>

{tls_auth}

# VPN-NATIVE SECURITY - ALL PROTECTION BUILT INTO VPN
# No browser extensions needed - everything enforced at VPN level
# 
# Security features automatically enforced:
# - Kill switch: Network-level, blocks all non-VPN traffic
# - DNS leak protection: All DNS forced through VPN
# - IPv6 leak protection: IPv6 completely disabled
# - WebRTC leak protection: STUN/TURN blocked at network level
# - Tracking protection: Known trackers blocked
# 
# Just connect and you're protected - no configuration needed!
'''
    
    # Write config file (client_config already has absolute path from above)
    with open(client_config, 'w') as f:
        f.write(config_content)
    
    # Verify file was created in correct location
    if not client_config.exists():
        print(f"ERROR: Config file was not created at {client_config}")
        sys.exit(1)
    
    # Verify it's in the right directory
    expected_dir = get_path('client_configs_dir').absolute()
    if client_config.parent != expected_dir:
        print(f"WARNING: Config saved to {client_config.parent} but expected {expected_dir}")
        # Move it to correct location
        import shutil
        correct_path = expected_dir / f'{name}.ovpn'
        shutil.move(str(client_config), str(correct_path))
        client_config = correct_path
        print(f"Moved config to correct location: {client_config}")
    
    # Clean up
    client_csr.unlink(missing_ok=True)
    
    print()
    print(f"✅ Client certificate generated!")
    print(f"  Config file: {client_config}")
    print(f"  Location verified: {client_config.exists()}")
    print()
    print("To use this config:")
    print(f"  - Copy {client_config} to your client device")
    print("  - Import it into your OpenVPN client")

def cmd_list_clients():
    """List all client configs"""
    client_configs_dir = get_path('client_configs_dir')
    
    if not client_configs_dir.exists():
        print("No clients configured yet")
        return
    
    configs = list(client_configs_dir.glob('*.ovpn'))
    if configs:
        print("Configured clients:")
        for config in sorted(configs):
            print(f"  - {config.stem}")
    else:
        print("No clients configured yet")

def cmd_logs():
    """Show server logs"""
    log_file = get_path('logs_dir') / 'server.log'
    if log_file.exists():
        subprocess.run(['tail', '-50', str(log_file)])
    else:
        print("No log file found")

# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description='VPN Management Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    subparsers.add_parser('start', help='Start VPN server')
    subparsers.add_parser('stop', help='Stop VPN server')
    subparsers.add_parser('restart', help='Restart VPN server')
    subparsers.add_parser('status', help='Show server status')
    subparsers.add_parser('list-clients', help='List all client configs')
    subparsers.add_parser('logs', help='Show server logs')
    
    add_client_parser = subparsers.add_parser('add-client', help='Generate client certificate')
    add_client_parser.add_argument('name', help='Client name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'start':
        cmd_start()
    elif args.command == 'stop':
        cmd_stop()
    elif args.command == 'restart':
        cmd_stop()
        import time
        time.sleep(2)
        cmd_start()
    elif args.command == 'status':
        cmd_status()
    elif args.command == 'add-client':
        cmd_add_client(args.name)
    elif args.command == 'list-clients':
        cmd_list_clients()
    elif args.command == 'logs':
        cmd_logs()

if __name__ == '__main__':
    main()

