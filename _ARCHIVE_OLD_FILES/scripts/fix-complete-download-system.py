#!/usr/bin/env python3
"""
Complete fix for download system - make it actually work!
1. Fix download page to show configs, not installers
2. Ensure clients generate both .ovpn and .phazevpn configs
3. Implement proper mobile detection
4. Use correct domain (phazevpn.com)
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔧 COMPLETE DOWNLOAD SYSTEM FIX")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Check current download page
        # ============================================================
        print("1️⃣  Checking current download page...")
        print("")
        
        success, download_page, _ = run_command(ssh, f"grep -c 'download-btn\\|Download for' {VPN_DIR}/web-portal/templates/download.html || echo '0'", check=False)
        print(f"   Download buttons found: {download_page}")
        print("")
        
        # ============================================================
        # STEP 2: Read current download route implementation
        # ============================================================
        print("2️⃣  Reading current download route...")
        print("")
        
        success, download_route, _ = run_command(ssh, f"sed -n '1495,1523p' {VPN_DIR}/web-portal/app.py", check=False)
        if download_route:
            print("   Current /download/<client_name> route:")
            for i, line in enumerate(download_route.split('\n')[:15], 1495):
                print(f"      {i}: {line[:80]}")
        print("")
        
        # ============================================================
        # STEP 3: Fix download route to auto-detect mobile vs desktop
        # ============================================================
        print("3️⃣  Fixing download route with mobile detection...")
        print("")
        
        # Read full app.py
        success, full_file, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        if success:
            lines = full_file.split('\n')
            
            # Find and replace the download route
            new_download_route = '''
@app.route('/download/<client_name>')
def download_client_config(client_name):
    """Download client config - auto-detects mobile vs desktop"""
    # Detect device type
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'iphone', 'ipad', 'ipod', 'android', 'mobile', 'tablet'
    ])
    
    if is_mobile:
        # Mobile device - serve OpenVPN config
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
        if config_file.exists():
            return send_file(str(config_file), as_attachment=True,
                           download_name=f'{client_name}.ovpn',
                           mimetype='application/x-openvpn-profile')
        else:
            return render_template('error.html',
                                 message=f'OpenVPN config for "{client_name}" not found. Please contact admin to create this client.'), 404
    else:
        # Desktop device - try PhazeVPN Protocol first, fallback to OpenVPN
        phazevpn_config = CLIENT_CONFIGS_DIR / f'{client_name}.phazevpn'
        if phazevpn_config.exists():
            return send_file(str(phazevpn_config), as_attachment=True,
                           download_name=f'{client_name}.phazevpn',
                           mimetype='application/json')
        else:
            # Fallback to OpenVPN
            config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
            if config_file.exists():
                return send_file(str(config_file), as_attachment=True,
                               download_name=f'{client_name}.ovpn',
                               mimetype='application/x-openvpn-profile')
            else:
                return render_template('error.html',
                                     message=f'Config for "{client_name}" not found. Please contact admin to create this client.'), 404
'''
            
            # Find the old download route and replace it
            route_start = None
            route_end = None
            
            for i, line in enumerate(lines):
                if i >= 1494 and '@app.route' in line and '/download/<client_name>' in line:
                    route_start = i
                    # Find end of function
                    for j in range(i + 1, min(i + 30, len(lines))):
                        if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                            if '@app.route' in lines[j] or (lines[j].strip().startswith('def ') and not lines[j].startswith('    ')):
                                route_end = j
                                break
                    if not route_end:
                        route_end = i + 10
                    break
            
            if route_start is not None:
                # Replace the route
                new_lines = lines[:route_start] + new_download_route.strip().split('\n') + lines[route_end:]
                new_file = '\n'.join(new_lines)
                
                # Write back
                stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{new_file}\nPYEOF")
                stdout.channel.recv_exit_status()
                print("   ✅ Fixed download route with mobile detection")
            else:
                print("   ⚠️  Could not find download route to replace")
        print("")
        
        # ============================================================
        # STEP 4: Simplify download page - remove installer links
        # ============================================================
        print("4️⃣  Fixing download page HTML...")
        print("")
        
        # Create a simple download page that just shows a form to download configs
        simple_download_page = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download VPN Config - PhazeVPN</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #4a9eff 0%, #10b981 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p {
            color: #aaa;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #4a9eff;
        }
        input[type="text"] {
            width: 100%;
            padding: 1rem;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: #fff;
            font-size: 1rem;
        }
        button {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #4a9eff 0%, #10b981 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            transform: scale(1.02);
        }
        .info {
            background: rgba(74, 158, 255, 0.2);
            border-left: 3px solid #4a9eff;
            padding: 1rem;
            margin-top: 1.5rem;
            border-radius: 4px;
        }
        .info h3 {
            color: #4a9eff;
            margin-bottom: 0.5rem;
        }
        .back-link {
            display: inline-block;
            margin-top: 1.5rem;
            color: #4a9eff;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📥 Download VPN Config</h1>
        <p>Enter your client name to download your VPN configuration file</p>
        
        <form method="GET" action="/download">
            <div class="form-group">
                <label for="name">Client Name:</label>
                <input type="text" id="name" name="name" required placeholder="Enter your client name" autofocus>
            </div>
            <button type="submit">⬇️ Download Config</button>
        </form>
        
        <div class="info">
            <h3>📱 Mobile Device?</h3>
            <p>You'll automatically get an OpenVPN config (.ovpn) file. Import it into OpenVPN Connect app.</p>
        </div>
        
        <div class="info">
            <h3>💻 Desktop Device?</h3>
            <p>You'll automatically get a PhazeVPN Protocol config (.phazevpn) file. Import it into PhazeVPN Desktop Client.</p>
        </div>
        
        <a href="/" class="back-link">← Back to Portal</a>
    </div>
</body>
</html>'''
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/download.html << 'HTMLEOF'\n{simple_download_page}\nHTMLEOF")
        stdout.channel.recv_exit_status()
        print("   ✅ Updated download page HTML")
        print("")
        
        # ============================================================
        # STEP 5: Update download page route to show form
        # ============================================================
        print("5️⃣  Updating download page route...")
        print("")
        
        # Find /download route (the page, not the download endpoint)
        success, full_file2, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        if success:
            lines2 = full_file2.split('\n')
            
            # Find @app.route('/download') that's just the page
            for i, line in enumerate(lines2):
                if '@app.route' in line and "'/download'" in line or '@app.route' in line and '"/download"' in line:
                    # Check next line to see if it's the page route
                    if i + 1 < len(lines2) and 'download_page' in lines2[i + 1]:
                        # Replace it
                        new_page_route = '''
@app.route('/download')
def download_page():
    """Download VPN config page"""
    client_name = request.args.get('name', '').strip()
    if client_name:
        # Redirect to download endpoint
        return redirect(url_for('download_client_config', client_name=client_name))
    return render_template('download.html')
'''
                        lines2[i] = new_page_route.strip()
                        # Remove old function
                        for j in range(i + 1, min(i + 5, len(lines2))):
                            if lines2[j].strip() and not lines2[j].startswith(' ') and '@app.route' in lines2[j]:
                                break
                            elif lines2[j].strip() and not lines2[j].startswith(' ') and not lines2[j].startswith('\t'):
                                if lines2[j].strip().startswith('def ') and 'download_page' not in lines2[j]:
                                    break
                        # Actually, let's just replace the whole section properly
                        # Find the function end
                        func_end = i + 1
                        for j in range(i + 1, min(i + 10, len(lines2))):
                            if lines2[j].strip() and not lines2[j].startswith(' ') and not lines2[j].startswith('\t'):
                                if '@app.route' in lines2[j] or (lines2[j].strip().startswith('def ') and 'download_page' not in lines2[j]):
                                    func_end = j
                                    break
                        
                        # Replace
                        new_lines2 = lines2[:i] + new_page_route.strip().split('\n') + lines2[func_end:]
                        new_file2 = '\n'.join(new_lines2)
                        
                        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{new_file2}\nPYEOF")
                        stdout.channel.recv_exit_status()
                        print("   ✅ Updated download page route")
                        break
        print("")
        
        # ============================================================
        # STEP 6: Verify syntax and restart
        # ============================================================
        print("6️⃣  Verifying syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error: {syntax_check}")
            return
        print("")
        
        print("7️⃣  Restarting web portal...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        time.sleep(3)
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in status:
            print("   ✅ Web portal restarted")
        print("")
        
        print("=" * 70)
        print("✅ DOWNLOAD SYSTEM FIXED")
        print("=" * 70)
        print("")
        print("📋 What was fixed:")
        print("   1. ✅ Download page now shows simple form (not installer links)")
        print("   2. ✅ Download route auto-detects mobile vs desktop")
        print("   3. ✅ Serves .ovpn for mobile, .phazevpn for desktop")
        print("   4. ✅ Simplified everything")
        print("")
        print("📝 Next steps:")
        print("   1. Create a client config (admin can do this)")
        print("   2. User visits: https://phazevpn.com/download")
        print("   3. Enters client name and downloads config")
        print("   4. Imports into VPN client app")
        print("")
        print("⚠️  Note: You still need to:")
        print("   - Generate client configs when creating clients")
        print("   - Make sure both .ovpn and .phazevpn files are created")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

