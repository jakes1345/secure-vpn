#!/usr/bin/env python3
"""
Generate PhazeVPN Protocol client configuration
Replaces OpenVPN .ovpn files with PhazeVPN Protocol JSON configs
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def generate_phazevpn_config(client_name, server_host, server_port=51821, username=None, password=None, output_dir=None):
    """
    Generate PhazeVPN Protocol client configuration
    
    Args:
        client_name: Name of the client
        server_host: VPN server hostname/IP
        server_port: VPN server port (default: 51821)
        username: Username for authentication (optional)
        password: Password for authentication (optional)
        output_dir: Directory to save config (default: current directory)
    """
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PhazeVPN Protocol config
    config = {
        "version": "1.0",
        "protocol": "phazevpn",
        "client_name": client_name,
        "server": {
            "host": server_host,
            "port": server_port,
            "protocol": "udp"
        },
        "authentication": {
            "username": username or client_name,
            "password": password  # In production, this should be hashed
        },
        "network": {
            "vpn_network": "10.9.0.0/24",
            "client_ip": "auto"  # Server will assign
        },
        "security": {
            "encryption": "ChaCha20-Poly1305",
            "key_exchange": "X25519",
            "perfect_forward_secrecy": True,
            "replay_protection": True
        },
        "features": {
            "traffic_obfuscation": True,
            "dpi_evasion": True,
            "zero_knowledge": True,
            "tor_ghost_mode": False  # Can be enabled per client
        },
        "generated": datetime.now().isoformat(),
        "notes": "PhazeVPN Protocol - Custom VPN Implementation"
    }
    
    # Save as JSON
    config_file = output_dir / f"{client_name}.phazevpn"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ PhazeVPN Protocol config generated: {config_file}")
    return config_file

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: generate-phazevpn-config.py <client_name> <server_host> [server_port] [username] [password]")
        print("Example: generate-phazevpn-config.py myclient phazevpn.duckdns.org 51821 myuser mypass")
        sys.exit(1)
    
    client_name = sys.argv[1]
    server_host = sys.argv[2]
    server_port = int(sys.argv[3]) if len(sys.argv) > 3 else 51821
    username = sys.argv[4] if len(sys.argv) > 4 else None
    password = sys.argv[5] if len(sys.argv) > 5 else None
    
    generate_phazevpn_config(client_name, server_host, server_port, username, password)

