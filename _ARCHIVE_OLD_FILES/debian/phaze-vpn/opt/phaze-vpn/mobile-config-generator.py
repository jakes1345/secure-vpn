#!/usr/bin/env python3
"""
PhazeVPN Mobile Config Generator
Generates iOS/Android VPN configurations
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import base64

BASE_DIR = Path('/opt/phaze-vpn') if Path('/opt/phaze-vpn').exists() else Path(__file__).parent.absolute()

def generate_ios_config(client_name: str, server_ip: str, server_port: int = 1194):
    """Generate iOS .mobileconfig file"""
    certs_dir = BASE_DIR / 'certs'
    client_configs_dir = BASE_DIR / 'client-configs'
    
    # Read certificates
    ca_crt = certs_dir / 'ca.crt'
    client_crt = certs_dir / f'{client_name}.crt'
    client_key = certs_dir / f'{client_name}.key'
    
    if not all(f.exists() for f in [ca_crt, client_crt, client_key]):
        print(f"Error: Certificates not found for {client_name}")
        return None
    
    # Read certificate contents
    with open(ca_crt) as f:
        ca_content = f.read().strip()
    with open(client_crt) as f:
        client_crt_content = f.read().strip()
    with open(client_key) as f:
        client_key_content = f.read().strip()
    
    # Remove headers/footers
    ca_content = ca_content.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').strip()
    client_crt_content = client_crt_content.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').strip()
    client_key_content = client_key_content.replace('-----BEGIN PRIVATE KEY-----', '').replace('-----END PRIVATE KEY-----', '').strip()
    
    # Generate mobileconfig XML
    mobileconfig = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>Password</key>
            <string></string>
            <key>PayloadCertificateFileName</key>
            <string>ca.crt</string>
            <key>PayloadContent</key>
            <data>
{base64.b64encode(ca_content.encode()).decode()}
            </data>
            <key>PayloadDescription</key>
            <string>PhazeVPN CA Certificate</string>
            <key>PayloadDisplayName</key>
            <string>PhazeVPN CA</string>
            <key>PayloadIdentifier</key>
            <string>com.phazevpn.ca</string>
            <key>PayloadType</key>
            <string>com.apple.security.root</string>
            <key>PayloadUUID</key>
            <string>CA-UUID-PLACEHOLDER</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
        <dict>
            <key>Password</key>
            <string></string>
            <key>PayloadCertificateFileName</key>
            <string>{client_name}.crt</string>
            <key>PayloadContent</key>
            <data>
{base64.b64encode(client_crt_content.encode()).decode()}
            </data>
            <key>PayloadDescription</key>
            <string>PhazeVPN Client Certificate</string>
            <key>PayloadDisplayName</key>
            <string>{client_name}</string>
            <key>PayloadIdentifier</key>
            <string>com.phazevpn.client.{client_name}</string>
            <key>PayloadType</key>
            <string>com.apple.security.certificate</string>
            <key>PayloadUUID</key>
            <string>CLIENT-UUID-PLACEHOLDER</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
        <dict>
            <key>UserPassword</key>
            <string></string>
            <key>PayloadCertificateFileName</key>
            <string>{client_name}.p12</string>
            <key>PayloadContent</key>
            <data>
{base64.b64encode(client_key_content.encode()).decode()}
            </data>
            <key>PayloadDescription</key>
            <string>PhazeVPN VPN Configuration</string>
            <key>PayloadDisplayName</key>
            <string>PhazeVPN</string>
            <key>PayloadIdentifier</key>
            <string>com.phazevpn.vpnconfig</string>
            <key>PayloadType</key>
            <string>com.apple.vpn.managed</string>
            <key>PayloadUUID</key>
            <string>VPN-UUID-PLACEHOLDER</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
            <key>VPN</key>
            <dict>
                <key>AuthName</key>
                <string>{client_name}</string>
                <key>AuthenticationMethod</key>
                <string>Certificate</string>
                <key>RemoteAddress</key>
                <string>{server_ip}</string>
                <key>RemoteIdentifier</key>
                <string>{server_ip}</string>
                <key>LocalIdentifier</key>
                <string>{client_name}</string>
                <key>PayloadCertificateUUID</key>
                <string>CLIENT-UUID-PLACEHOLDER</string>
                <key>OnDemandEnabled</key>
                <integer>0</integer>
                <key>VPNType</key>
                <string>IKEv2</string>
            </dict>
        </dict>
    </array>
    <key>PayloadDescription</key>
    <string>PhazeVPN Configuration for {client_name}</string>
    <key>PayloadDisplayName</key>
    <string>PhazeVPN</string>
    <key>PayloadIdentifier</key>
    <string>com.phazevpn</string>
    <key>PayloadOrganization</key>
    <string>PhazeVPN</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>CONFIG-UUID-PLACEHOLDER</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>'''
    
    # Save mobileconfig
    output_file = client_configs_dir / f'{client_name}.mobileconfig'
    with open(output_file, 'w') as f:
        f.write(mobileconfig)
    
    print(f"✅ iOS config generated: {output_file}")
    return output_file

def generate_android_config(client_name: str, server_ip: str, server_port: int = 1194):
    """Generate Android OpenVPN config"""
    # Android uses standard .ovpn files
    # Just ensure it's optimized for mobile
    certs_dir = BASE_DIR / 'certs'
    client_configs_dir = BASE_DIR / 'client-configs'
    
    ca_crt = certs_dir / 'ca.crt'
    client_crt = certs_dir / f'{client_name}.crt'
    client_key = certs_dir / f'{client_name}.key'
    ta_key = certs_dir / 'ta.key'
    
    if not all(f.exists() for f in [ca_crt, client_crt, client_key]):
        print(f"Error: Certificates not found for {client_name}")
        return None
    
    # Read certificates
    with open(ca_crt) as f:
        ca_content = f.read()
    with open(client_crt) as f:
        client_crt_content = f.read()
    with open(client_key) as f:
        client_key_content = f.read()
    
    ta_content = ''
    if ta_key.exists():
        with open(ta_key) as f:
            ta_content = f.read()
    
    # Generate Android-optimized config
    config_content = f'''# PhazeVPN Android Configuration for {client_name}
# Optimized for mobile devices

client
dev tun
proto udp
remote {server_ip} {server_port}
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server

# Mobile-optimized encryption (ChaCha20 is faster on mobile)
data-ciphers CHACHA20-POLY1305:AES-256-GCM
cipher CHACHA20-POLY1305
auth SHA256
tls-version-min 1.2

# Mobile optimizations
comp-lzo no
push "comp-lzo no"

# DNS
block-outside-dns
redirect-gateway def1
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "block-ipv6"

# Keepalive for mobile (handles network switching)
keepalive 10 120

# Mobile-specific: Allow reconnection on network change
persist-remote-ip
resolv-retry infinite

<ca>
{ca_content}</ca>

<cert>
{client_crt_content}</cert>

<key>
{client_key_content}</key>
'''
    
    if ta_content:
        config_content += f'''
<tls-auth>
{ta_content}</tls-auth>
key-direction 1
'''
    
    # Save config
    output_file = client_configs_dir / f'{client_name}-android.ovpn'
    with open(output_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Android config generated: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate mobile VPN configs')
    parser.add_argument('client_name', help='Client name')
    parser.add_argument('--server-ip', required=True, help='Server IP address')
    parser.add_argument('--server-port', type=int, default=1194, help='Server port')
    parser.add_argument('--platform', choices=['ios', 'android', 'both'], default='both',
                       help='Platform to generate config for')
    
    args = parser.parse_args()
    
    if args.platform in ['ios', 'both']:
        generate_ios_config(args.client_name, args.server_ip, args.server_port)
    
    if args.platform in ['android', 'both']:
        generate_android_config(args.client_name, args.server_ip, args.server_port)

if __name__ == '__main__':
    main()

