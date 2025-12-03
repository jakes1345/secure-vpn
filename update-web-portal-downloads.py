#!/usr/bin/env python3
"""
Update web portal download routes for PhazeVPN Protocol
"""

import re
from pathlib import Path

app_file = Path('web-portal/app.py')

print("🔧 Updating web portal download routes...")

content = app_file.read_text()

# Update download route to prioritize PhazeVPN Protocol
download_route_pattern = r'@app\.route\(\'/download/client/<platform>\'\)\ndef download_client\(platform\):.*?return.*?\n'

new_download_route = '''@app.route('/download/client/<platform>')
def download_client(platform):
    """Download PhazeVPN Protocol client installer for specific platform"""
    platform = platform.lower()
    
    # PhazeVPN Protocol is the main VPN now
    # Desktop users get PhazeVPN Protocol
    # Mobile users get OpenVPN/WireGuard (temporary)
    
    VPN_DIR = Path(VPN_CONFIG.get('vpn_dir', '/opt/secure-vpn'))
    BASE_DIR = Path(__file__).parent.parent
    
    installer_file = None
    installer_name = None
    
    if platform in ['linux', 'ubuntu', 'debian']:
        # Ubuntu/Debian .deb package for PhazeVPN Protocol
        installer_paths = [
            VPN_DIR / 'downloads' / 'installers' / 'phazevpn-client_1.0.0_amd64.deb',
            BASE_DIR / 'build-output' / 'phazevpn-client_1.0.0_amd64.deb',
            BASE_DIR / 'phazevpn-client' / 'installers' / 'phazevpn-client_1.0.0_amd64.deb'
        ]
        installer_name = 'phazevpn-client_1.0.0_amd64.deb'
        installer_file = next((p for p in installer_paths if p.exists()), None)
    
    elif platform in ['macos', 'mac', 'darwin']:
        # macOS .app bundle or .pkg
        installer_paths = [
            VPN_DIR / 'downloads' / 'installers' / 'PhazeVPN.app.tar.gz',
            VPN_DIR / 'downloads' / 'installers' / 'phazevpn-client-macos.pkg',
            BASE_DIR / 'build-output' / 'PhazeVPN.app.tar.gz',
            BASE_DIR / 'build-output' / 'PhazeVPN.app'
        ]
        installer_name = 'PhazeVPN.app.tar.gz'
        installer_file = next((p for p in installer_paths if p.exists()), None)
    
    elif platform in ['windows', 'win', 'exe']:
        # Windows .exe installer
        installer_paths = [
            VPN_DIR / 'downloads' / 'installers' / 'phazevpn-client-installer.exe',
            VPN_DIR / 'downloads' / 'installers' / 'phazevpn-client-windows.zip',
            BASE_DIR / 'build-output' / 'phazevpn-client-windows.zip'
        ]
        installer_name = 'phazevpn-client-installer.exe'
        installer_file = next((p for p in installer_paths if p.exists()), None)
    
    # If installer found, serve it
    if installer_file and installer_file.exists():
        return send_file(
            str(installer_file),
            as_attachment=True,
            download_name=installer_name,
            mimetype='application/octet-stream'
        )
    
    # Fallback: serve Python client script
    client_file = None
    client_paths = [
        VPN_DIR / 'phazevpn-protocol' / 'phazevpn-client.py',
        BASE_DIR / 'phazevpn-protocol' / 'phazevpn-client.py'
    ]
    client_file = next((p for p in client_paths if p.exists()), None)
    
    if client_file and client_file.exists():
        return send_file(
            str(client_file),
            as_attachment=True,
            download_name='phazevpn-client.py',
            mimetype='text/x-python'
        )
    
    # No files found
    return render_template('download-instructions.html',
                         platform=platform.title(),
                         instructions=f"PhazeVPN Protocol installer for {platform} is not yet available. Please contact support or use the Python client.")
'''

# Replace the download route
if re.search(r'@app\.route\(\'/download/client/<platform>\'\)', content):
    content = re.sub(
        r'@app\.route\(\'/download/client/<platform>\'\).*?(?=\n@app\.route|\nif __name__|\Z)',
        new_download_route,
        content,
        flags=re.DOTALL
    )
    print("   ✅ Updated download route")
else:
    # Insert after download_page route
    insert_after = r'(@app\.route\(\'/download\'\)\ndef download_page\(\):.*?\n    return render_template\(\'download\.html\'\))'
    content = re.sub(
        insert_after,
        r'\1\n\n' + new_download_route,
        content,
        flags=re.DOTALL
    )
    print("   ✅ Added download route")

app_file.write_text(content)
print("✅ Web portal updated!")

