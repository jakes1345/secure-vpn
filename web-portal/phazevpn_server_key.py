#!/usr/bin/env python3
"""
PhazeVPN Server Key Management
Retrieves the real server public key for PhazeVPN protocol
"""

import subprocess
import base64
from pathlib import Path
import os

# Possible server key locations
SERVER_KEY_PATHS = [
    Path("/etc/phazevpn/wireguard/server_public.key"),
    Path("/opt/phaze-vpn/wireguard/server_public.key"),
    Path("/opt/secure-vpn/wireguard/server_public.key"),
    Path("/opt/phaze-vpn/phazevpn-protocol-go/server_public.key"),
    Path("/opt/secure-vpn/phazevpn-protocol-go/server_public.key"),
]

def get_phazevpn_server_public_key() -> str:
    """
    Get PhazeVPN server public key
    
    Returns:
        Server public key (base64 encoded) or empty string if not found
    """
    # Try reading from file
    for key_path in SERVER_KEY_PATHS:
        if key_path.exists():
            try:
                key = key_path.read_text().strip()
                if key:
                    return key
            except Exception as e:
                print(f"⚠️  Error reading {key_path}: {e}")
    
    # Try querying running server (if API endpoint exists)
    # This would require the server to expose its public key via API
    # For now, we'll need to generate/store it
    
    # Try WireGuard server key (PhazeVPN uses same key format)
    try:
        result = subprocess.run(
            ['wg', 'show', 'wg0', 'public-key'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            key = result.stdout.strip()
            if key:
                return key
    except:
        pass
    
    # If not found, return empty (will use placeholder)
    return ""

def ensure_server_key_exists() -> bool:
    """
    Ensure server public key file exists
    Creates it if missing by querying server or generating
    
    Returns:
        True if key exists or was created
    """
    # Check if any key file exists
    for key_path in SERVER_KEY_PATHS:
        if key_path.exists():
            return True
    
    # Try to get from WireGuard
    try:
        result = subprocess.run(
            ['wg', 'show', 'wg0', 'public-key'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            key = result.stdout.strip()
            if key:
                # Save to first location
                key_path = SERVER_KEY_PATHS[0]
                key_path.parent.mkdir(parents=True, exist_ok=True)
                key_path.write_text(key)
                key_path.chmod(0o644)
                return True
    except:
        pass
    
    # Could also query PhazeVPN server API if it exposes public key
    # For now, return False (key needs to be set up)
    return False

if __name__ == '__main__':
    print("=" * 80)
    print("🔑 PHAZEVPN SERVER KEY RETRIEVAL")
    print("=" * 80)
    print()
    
    key = get_phazevpn_server_public_key()
    
    if key:
        print(f"✅ Server public key found:")
        print(f"   {key[:50]}...")
        print()
        print("Key locations checked:")
        for path in SERVER_KEY_PATHS:
            exists = "✅" if path.exists() else "❌"
            print(f"   {exists} {path}")
    else:
        print("❌ Server public key not found")
        print()
        print("To set up:")
        print("  1. Run PhazeVPN server to generate key")
        print("  2. Or use WireGuard key: wg show wg0 public-key")
        print("  3. Save to: /etc/phazevpn/wireguard/server_public.key")
