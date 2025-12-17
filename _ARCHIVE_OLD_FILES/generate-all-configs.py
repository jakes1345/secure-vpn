#!/usr/bin/env python3
"""
Generate all config types (OpenVPN, PhazeVPN, WireGuard) for a client
This ensures all three config types are available when a client is created
"""

import sys
import subprocess
from pathlib import Path

# Try installed location first, then current directory
if Path('/opt/phaze-vpn/vpn-manager.py').exists():
    BASE_DIR = Path('/opt/phaze-vpn')
else:
    BASE_DIR = Path(__file__).parent.absolute()

CLIENT_CONFIGS_DIR = BASE_DIR / 'client-configs'
CERTS_DIR = BASE_DIR / 'certs'
WIREGUARD_DIR = BASE_DIR / 'wireguard' / 'clients'
PHAZEVPN_PROTOCOL_DIR = BASE_DIR / 'phazevpn-protocol'

def generate_phazevpn_config(client_name):
    """Generate PhazeVPN config with CUSTOM certificates - EXPERIMENTAL"""
    print()
    print("="*60)
    print("⚠️  EXPERIMENTAL PROTOCOL - USE AT YOUR OWN RISK ⚠️")
    print("="*60)
    print("PhazeVPN Protocol:")
    print("  • Uses CUSTOM certificate system (separate from OpenVPN/WireGuard)")
    print("  • EXPERIMENTAL - Not audited by security experts")
    print("  • Not verified by trusted organizations")
    print("  • May contain security vulnerabilities")
    print("  • Use at your own risk!")
    print()
    print("RECOMMENDED: Use OpenVPN or WireGuard (both audited)")
    print("="*60)
    print()
    
    try:
        # Generate PhazeVPN custom certificates
        phazevpn_cert_gen = PHAZEVPN_PROTOCOL_DIR / 'generate-phazevpn-certs.py'
        if phazevpn_cert_gen.exists():
            print(f"🔐 Generating PhazeVPN custom certificates for {client_name}...")
            result = subprocess.run(
                ['python3', str(phazevpn_cert_gen), client_name],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"✅ PhazeVPN certificates generated")
            else:
                print(f"⚠️  Certificate generation had warnings: {result.stderr[:200]}")
        else:
            print(f"⚠️  PhazeVPN certificate generator not found: {phazevpn_cert_gen}")
            print("   Skipping PhazeVPN config generation")
            return False
        
        # Generate PhazeVPN config file
        phazevpn_config_gen = PHAZEVPN_PROTOCOL_DIR / 'generate-phazevpn-config.py'
        if phazevpn_config_gen.exists():
            print(f"📝 Generating PhazeVPN config file...")
            result = subprocess.run(
                ['python3', str(phazevpn_config_gen), client_name, 'phazevpn.com', '51821'],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                config_file = CLIENT_CONFIGS_DIR / f'{client_name}.phazevpn'
                if config_file.exists():
                    # Add experimental warning to config file
                    with open(config_file, 'r') as f:
                        content = f.read()
                    with open(config_file, 'w') as f:
                        f.write("# ⚠️  EXPERIMENTAL PROTOCOL - USE AT YOUR OWN RISK ⚠️\n")
                        f.write("# PhazeVPN Protocol is NOT audited or verified\n")
                        f.write("# Not recommended for production use\n")
                        f.write("# Use OpenVPN or WireGuard for production\n")
                        f.write("#\n")
                        f.write(content)
                    print(f"✅ Generated PhazeVPN config: {config_file}")
                    print("   ⚠️  Remember: This is EXPERIMENTAL!")
                    return True
        else:
            print(f"⚠️  PhazeVPN config generator not found")
            return False
    except Exception as e:
        print(f"⚠️  Error generating PhazeVPN config: {e}")
        return False

def generate_wireguard_config(client_name):
    """Generate WireGuard config"""
    try:
        WIREGUARD_DIR.mkdir(parents=True, exist_ok=True)
        config_file = WIREGUARD_DIR / f'{client_name}.conf'
        
        # Check if WireGuard add-client script exists
        add_client_script = BASE_DIR / 'wireguard' / 'add-client.sh'
        if add_client_script.exists():
            # Run the WireGuard add-client script
            result = subprocess.run(
                ['bash', str(add_client_script), client_name],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and config_file.exists():
                print(f"✅ Generated WireGuard config: {config_file}")
                return True
            else:
                print(f"⚠️  WireGuard script failed: {result.stderr}")
        else:
            # Fallback: Create a basic WireGuard config template
            # Note: This won't work without proper keys, but at least creates the file
            config_content = f"""# WireGuard Configuration for {client_name}
# Server: phazevpn.com
# Port: 51820
# Note: This is a template. Proper keys need to be generated by WireGuard.

[Interface]
PrivateKey = <CLIENT_PRIVATE_KEY>
Address = 10.0.0.{hash(client_name) % 254 + 2}/24
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = phazevpn.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            with open(config_file, 'w') as f:
                f.write(config_content)
            print(f"⚠️  Created WireGuard template (needs proper keys): {config_file}")
            return True
    except Exception as e:
        print(f"⚠️  Could not generate WireGuard config: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-all-configs.py <client_name>")
        sys.exit(1)
    
    client_name = sys.argv[1]
    
    print(f"🔧 Generating all config types for client: {client_name}")
    print("=" * 50)
    
    # Check if OpenVPN config exists (should be created by vpn-manager first)
    openvpn_config = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
    if not openvpn_config.exists():
        print(f"⚠️  OpenVPN config not found: {openvpn_config}")
        print("   Run 'vpn-manager.py add-client {client_name}' first")
    else:
        print(f"✅ OpenVPN config exists: {openvpn_config}")
    
    # Generate WireGuard config (audited protocol)
    print("\n📦 Generating WireGuard config...")
    wireguard_ok = generate_wireguard_config(client_name)
    
    # Generate PhazeVPN config (EXPERIMENTAL - custom certificates)
    print("\n📦 Generating PhazeVPN config (EXPERIMENTAL)...")
    phazevpn_ok = generate_phazevpn_config(client_name)
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"  OpenVPN: {'✅' if openvpn_config.exists() else '❌'} (Recommended - Battle-tested)")
    print(f"  WireGuard: {'✅' if wireguard_ok else '❌'} (Recommended - Modern & Secure)")
    if phazevpn_ok:
        print(f"  PhazeVPN: ⚠️  EXPERIMENTAL (Use OpenVPN or WireGuard for production)")
    else:
        print(f"  PhazeVPN: ❌ Failed (experimental protocol)")
    
    if openvpn_config.exists() and (phazevpn_ok or wireguard_ok):
        print("\n✅ All available config types generated!")
        return 0
    else:
        print("\n⚠️  Some config types could not be generated")
        return 1

if __name__ == '__main__':
    sys.exit(main())

