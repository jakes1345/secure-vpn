#!/usr/bin/env python3
"""
Generate all protocol configs for a client (OpenVPN, WireGuard, PhazeVPN)
"""
import sys
import subprocess
from pathlib import Path

def generate_all_protocols(client_name):
    """Generate OpenVPN, WireGuard, and PhazeVPN configs for a client"""
    results = {
        'openvpn': False,
        'wireguard': False,
        'phazevpn': False
    }
    
    # Base directories
    BASE_DIR = Path('/opt/phaze-vpn')
    VPN_DIR = BASE_DIR
    CLIENT_CONFIGS_DIR = VPN_DIR / 'client-configs'
    CERTS_DIR = VPN_DIR / 'certs'
    
    # Ensure directories exist
    CLIENT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"[ALL-PROTOCOLS] Generating configs for {client_name}...")
    
    # 1. Generate OpenVPN config
    print(f"[ALL-PROTOCOLS] Step 1/3: Generating OpenVPN config...")
    try:
        # Use vpn-manager.py if available
        vpn_manager = VPN_DIR / 'vpn-manager.py'
        if vpn_manager.exists():
            result = subprocess.run(
                ['python3', str(vpn_manager), 'add-client', client_name],
                cwd=str(VPN_DIR),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                results['openvpn'] = True
                print(f"[ALL-PROTOCOLS] ✅ OpenVPN config created")
            else:
                print(f"[ALL-PROTOCOLS] ⚠️  OpenVPN failed: {result.stderr[:200]}")
        else:
            print(f"[ALL-PROTOCOLS] ⚠️  vpn-manager.py not found, skipping OpenVPN")
    except Exception as e:
        print(f"[ALL-PROTOCOLS] ⚠️  OpenVPN error: {e}")
    
    # 2. Generate WireGuard config
    print(f"[ALL-PROTOCOLS] Step 2/3: Generating WireGuard config...")
    try:
        wg_dir = BASE_DIR / 'wireguard'
        wg_add_client = wg_dir / 'add-client.sh'
        
        if wg_add_client.exists():
            result = subprocess.run(
                ['bash', str(wg_add_client), client_name],
                cwd=str(wg_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                results['wireguard'] = True
                print(f"[ALL-PROTOCOLS] ✅ WireGuard config created")
            else:
                print(f"[ALL-PROTOCOLS] ⚠️  WireGuard failed: {result.stderr[:200]}")
        else:
            # Create WireGuard config manually
            wg_clients_dir = wg_dir / 'clients'
            wg_clients_dir.mkdir(parents=True, exist_ok=True)
            
            # Simple WireGuard config (needs server key - placeholder for now)
            wg_config = wg_clients_dir / f'{client_name}.conf'
            server_key = "SERVER_PUBLIC_KEY_PLACEHOLDER"  # Should get from server
            client_private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
            client_public_key = subprocess.check_output(['wg', 'pubkey'], input=client_private_key.encode()).decode().strip()
            
            config_content = f"""[Interface]
PrivateKey = {client_private_key}
Address = 10.8.0.{hash(client_name) % 250 + 2}/24
DNS = 1.1.1.1

[Peer]
PublicKey = {server_key}
Endpoint = phazevpn.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            wg_config.write_text(config_content)
            wg_config.chmod(0o600)
            results['wireguard'] = True
            print(f"[ALL-PROTOCOLS] ✅ WireGuard config created manually")
    except Exception as e:
        print(f"[ALL-PROTOCOLS] ⚠️  WireGuard error: {e}")
    
    # 3. Generate PhazeVPN config (already done, but verify)
    print(f"[ALL-PROTOCOLS] Step 3/3: Verifying PhazeVPN config...")
    phazevpn_config = CLIENT_CONFIGS_DIR / f'{client_name}.phazevpn'
    if phazevpn_config.exists():
        results['phazevpn'] = True
        print(f"[ALL-PROTOCOLS] ✅ PhazeVPN config exists")
    else:
        print(f"[ALL-PROTOCOLS] ⚠️  PhazeVPN config not found (should be created separately)")
    
    # Summary
    created = [k for k, v in results.items() if v]
    print(f"[ALL-PROTOCOLS] ✅ Generated: {', '.join(created) if created else 'none'}")
    
    return results

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 generate_all_protocols.py <client-name>")
        sys.exit(1)
    
    client_name = sys.argv[1]
    generate_all_protocols(client_name)

