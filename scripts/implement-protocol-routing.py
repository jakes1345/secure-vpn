#!/usr/bin/env python3
"""
Implement protocol routing: PhazeVPN Protocol for desktop, OpenVPN for mobile
"""

import paramiko
import sys

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
    print("🔧 IMPLEMENTING PROTOCOL ROUTING")
    print("   Desktop → PhazeVPN Protocol | Mobile → OpenVPN")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check current download route
        print("1️⃣  Checking current download route implementation...")
        print("")
        
        success, download_code, _ = run_command(ssh, f"grep -A 30 '@app.route.*download' {VPN_DIR}/web-portal/app.py | head -40", check=False)
        if download_code:
            print("   Current download route found")
        else:
            print("   ⚠️  Download route not found")
        print("")
        
        # Add mobile detection function
        print("2️⃣  Adding mobile device detection function...")
        print("")
        
        detection_function = '''
def is_mobile_device(user_agent: str) -> bool:
    """Detect if client is mobile device based on User-Agent"""
    if not user_agent:
        return False
    user_agent_lower = user_agent.lower()
    mobile_keywords = [
        'iphone', 'ipad', 'ipod',
        'android', 'mobile', 'tablet',
        'windows phone', 'blackberry',
        'opera mini', 'kindle', 'silk'
    ]
    return any(keyword in user_agent_lower for keyword in mobile_keywords)
'''
        
        # Read app.py and insert function before download route
        success, full_file, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        if success:
            # Find where to insert (before download route)
            lines = full_file.split('\n')
            insert_index = None
            
            for i, line in enumerate(lines):
                if '@app.route' in line and '/download' in line:
                    insert_index = i
                    break
            
            if insert_index:
                # Insert function before download route
                function_lines = detection_function.strip().split('\n')
                for j, func_line in enumerate(function_lines):
                    lines.insert(insert_index + j, func_line)
                
                new_file = '\n'.join(lines)
                
                # Write back
                stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{new_file}\nPYEOF")
                stdout.channel.recv_exit_status()
                print("   ✅ Added mobile detection function")
            else:
                print("   ⚠️  Could not find download route to insert function")
        print("")
        
        # Update download route to use mobile detection
        print("3️⃣  Updating download route to route by device type...")
        print("")
        
        # Find and update download route
        success, download_route, _ = run_command(ssh, f"grep -n '@app.route.*download' {VPN_DIR}/web-portal/app.py", check=False)
        if download_route:
            print(f"   Download route found at: {download_route}")
            
            # Read lines around download route
            line_num = int(download_route.split(':')[0])
            success2, route_section, _ = run_command(ssh, f"sed -n '{line_num},{line_num + 50}p' {VPN_DIR}/web-portal/app.py", check=False)
            
            if route_section:
                print("   Current download route:")
                for i, line in enumerate(route_section.split('\n')[:20], line_num):
                    print(f"      {i}: {line[:80]}")
                
                # Update the route to detect mobile and route accordingly
                print("")
                print("   🔧 Updating route to detect mobile vs desktop...")
                
                # Read full file again
                success3, full_file2, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
                
                if success3:
                    # Replace download route logic
                    updated_route = '''
@app.route('/download')
def download():
    """Download client config - auto-detects mobile vs desktop"""
    client_name = request.args.get('name', '')
    if not client_name:
        return render_template('error.html', message='Client name required'), 400
    
    # Detect device type
    user_agent = request.headers.get('User-Agent', '')
    is_mobile = is_mobile_device(user_agent)
    
    if is_mobile:
        # Mobile device - serve OpenVPN config
        config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
        if config_file.exists():
            return send_file(str(config_file), as_attachment=True, 
                           download_name=f'{client_name}.ovpn',
                           mimetype='application/x-openvpn-profile')
        else:
            return render_template('error.html', 
                                 message=f'OpenVPN config for {client_name} not found. Mobile devices use OpenVPN.'), 404
    else:
        # Desktop device - serve PhazeVPN Protocol config
        # Try PhazeVPN Protocol config first
        phazevpn_config = CLIENT_CONFIGS_DIR / f'{client_name}.phazevpn'
        if phazevpn_config.exists():
            return send_file(str(phazevpn_config), as_attachment=True,
                           download_name=f'{client_name}.phazevpn',
                           mimetype='application/json')
        else:
            # Fallback to OpenVPN if PhazeVPN config doesn't exist
            config_file = CLIENT_CONFIGS_DIR / f'{client_name}.ovpn'
            if config_file.exists():
                return send_file(str(config_file), as_attachment=True,
                               download_name=f'{client_name}.ovpn',
                               mimetype='application/x-openvpn-profile')
            else:
                return render_template('error.html',
                                     message=f'Config for {client_name} not found'), 404
'''
                    
                    # Find and replace download route
                    lines2 = full_file2.split('\n')
                    route_start = None
                    route_end = None
                    
                    for i, line in enumerate(lines2):
                        if '@app.route' in line and '/download' in line:
                            route_start = i
                            # Find end of function (next @app.route or end of file)
                            for j in range(i + 1, min(i + 100, len(lines2))):
                                if lines2[j].strip() and not lines2[j].startswith(' ') and not lines2[j].startswith('\t'):
                                    if '@app.route' in lines2[j] or 'def ' in lines2[j] and not lines2[j].startswith('    '):
                                        route_end = j
                                        break
                            if not route_end:
                                route_end = i + 50
                            break
                    
                    if route_start is not None:
                        # Replace the route
                        new_lines = lines2[:route_start] + updated_route.strip().split('\n') + lines2[route_end:]
                        new_file2 = '\n'.join(new_lines)
                        
                        # Write back
                        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{new_file2}\nPYEOF")
                        stdout.channel.recv_exit_status()
                        print("   ✅ Updated download route with mobile detection")
        print("")
        
        # Verify syntax
        print("4️⃣  Verifying Python syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error: {syntax_check}")
            return
        print("")
        
        # Check what ports/services are running
        print("5️⃣  Checking VPN service status...")
        print("")
        
        # Check PhazeVPN Protocol
        success, phazevpn_status, _ = run_command(ssh, "systemctl is-active phazevpn-protocol 2>&1 || echo 'NOT_ACTIVE'", check=False)
        if 'active' in phazevpn_status:
            print("   ✅ PhazeVPN Protocol service is running")
            success2, phazevpn_port, _ = run_command(ssh, "netstat -tuln | grep phazevpn || ss -tuln | grep -E ':(443|51820|51821)' | head -2", check=False)
            if phazevpn_port:
                print(f"      Listening on: {phazevpn_port[:100]}")
        else:
            print("   ⚠️  PhazeVPN Protocol service is not running")
        
        # Check OpenVPN
        success, openvpn_status, _ = run_command(ssh, "systemctl is-active openvpn@server 2>&1 || echo 'NOT_ACTIVE'", check=False)
        if 'active' in openvpn_status:
            print("   ✅ OpenVPN service is running")
            success2, openvpn_port, _ = run_command(ssh, "netstat -tuln | grep :1194 || ss -tuln | grep :1194", check=False)
            if openvpn_port:
                print(f"      Listening on port 1194")
        else:
            print("   ⚠️  OpenVPN service is not running")
        print("")
        
        # Restart web portal
        print("6️⃣  Restarting web portal...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        
        import time
        time.sleep(3)
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in status:
            print("   ✅ Web portal restarted")
        print("")
        
        print("=" * 70)
        print("✅ PROTOCOL ROUTING IMPLEMENTED")
        print("=" * 70)
        print("")
        print("📋 How it works:")
        print("   1. Desktop clients download → PhazeVPN Protocol config (.phazevpn)")
        print("   2. Mobile clients download → OpenVPN config (.ovpn)")
        print("   3. Auto-detection via User-Agent header")
        print("")
        print("🔌 Ports:")
        print("   - PhazeVPN Protocol: Port 443 (desktop)")
        print("   - OpenVPN: Port 1194 (mobile)")
        print("")
        print("📱 Test mobile download:")
        print("   curl -A 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)' \\")
        print("        https://phazevpn.com/download?name=CLIENT_NAME")
        print("")
        print("💻 Test desktop download:")
        print("   curl -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' \\")
        print("        https://phazevpn.com/download?name=CLIENT_NAME")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

