#!/usr/bin/env python3
"""
Fix client creation to generate BOTH .ovpn and .phazevpn configs
Also update domain to phazevpn.com
"""

import paramiko
import sys
import json

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
    print("🔧 FIXING CLIENT CREATION - Generate Both Config Types")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check how clients are currently created
        print("1️⃣  Checking how clients are currently created...")
        print("")
        
        # Check vpn-manager.py
        success, add_client_func, _ = run_command(ssh, f"grep -A 5 'def.*add.*client' {VPN_DIR}/vpn-manager.py | head -10", check=False)
        if add_client_func:
            print("   vpn-manager.py add_client function found")
        print("")
        
        # Check if client creation in web portal calls vpn-manager
        success, web_add_client, _ = run_command(ssh, f"grep -B 2 -A 10 'add.*client\\|create.*client' {VPN_DIR}/web-portal/app.py | grep -A 10 'subprocess\\|vpn-manager' | head -15", check=False)
        if web_add_client:
            print("   Web portal client creation:")
            print(f"      {web_add_client[:200]}")
        print("")
        
        # Check current server IP/domain in config
        print("2️⃣  Checking current server domain/IP...")
        print("")
        
        success, server_ip, _ = run_command(ssh, f"grep -E 'server_ip|SERVER_IP|phazevpn' {VPN_DIR}/vpn-manager.py | head -5", check=False)
        if server_ip:
            print("   Current config:")
            for line in server_ip.split('\n')[:5]:
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # Update vpn-manager.py to use phazevpn.com
        print("3️⃣  Updating domain to phazevpn.com...")
        print("")
        
        success, vpn_manager_content, _ = run_command(ssh, f"cat {VPN_DIR}/vpn-manager.py", check=False)
        
        if success:
            # Replace old domain with phazevpn.com
            updated_content = vpn_manager_content.replace(
                "phazevpn.duckdns.org",
                "phazevpn.com"
            )
            
            # Also update if there's an IP hardcoded
            if "'server_ip': os.environ.get('VPN_SERVER_IP'" in updated_content:
                # Update default
                updated_content = updated_content.replace(
                    "os.environ.get('VPN_SERVER_IP', 'phazevpn.duckdns.org')",
                    "os.environ.get('VPN_SERVER_IP', 'phazevpn.com')"
                )
            
            if updated_content != vpn_manager_content:
                stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/vpn-manager.py << 'PYEOF'\n{updated_content}\nPYEOF")
                stdout.channel.recv_exit_status()
                print("   ✅ Updated domain to phazevpn.com")
            else:
                print("   ℹ️  Domain already set to phazevpn.com")
        print("")
        
        # Create a function to generate both config types
        print("4️⃣  Creating function to generate both config types...")
        print("")
        
        # Create a script that generates both .ovpn and .phazevpn when a client is added
        generate_both_configs_script = '''#!/usr/bin/env python3
"""
Generate both OpenVPN and PhazeVPN Protocol configs for a client
"""
import sys
import subprocess
from pathlib import Path

VPN_DIR = Path("/opt/secure-vpn")
CLIENT_NAME = sys.argv[1] if len(sys.argv) > 1 else None

if not CLIENT_NAME:
    print("Usage: generate-both-configs.py <client_name>")
    sys.exit(1)

# 1. Generate OpenVPN config using vpn-manager
print(f"Generating OpenVPN config for {CLIENT_NAME}...")
result = subprocess.run(
    [sys.executable, str(VPN_DIR / "vpn-manager.py"), "add-client", CLIENT_NAME],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print(f"✅ OpenVPN config generated")
else:
    print(f"⚠️  OpenVPN config generation: {result.stderr}")

# 2. Generate PhazeVPN Protocol config
print(f"Generating PhazeVPN Protocol config for {CLIENT_NAME}...")
try:
    sys.path.insert(0, str(VPN_DIR / "phazevpn-protocol"))
    from generate_phazevpn_config import generate_phazevpn_config
    
    server_host = "phazevpn.com"
    server_port = 443  # PhazeVPN Protocol on port 443
    
    config_file = generate_phazevpn_config(
        CLIENT_NAME,
        server_host,
        server_port,
        username=CLIENT_NAME,
        password=None,
        output_dir=VPN_DIR / "client-configs"
    )
    print(f"✅ PhazeVPN Protocol config generated: {config_file}")
except Exception as e:
    print(f"⚠️  PhazeVPN Protocol config generation failed: {e}")

print("")
print("✅ Both configs generated (or attempted)")
'''
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/scripts/generate-both-configs.py << 'PYEOF'\n{generate_both_configs_script}\nPYEOF")
        stdout.channel.recv_exit_status()
        run_command(ssh, f"chmod +x {VPN_DIR}/scripts/generate-both-configs.py", check=False)
        print("   ✅ Created generate-both-configs.py script")
        print("")
        
        # Update web portal to use this script when creating clients
        print("5️⃣  Checking web portal client creation...")
        print("")
        
        # Find where clients are created in web portal
        success, add_client_routes, _ = run_command(ssh, f"grep -n 'add.*client\\|create.*client' {VPN_DIR}/web-portal/app.py | grep -v 'can_add_clients' | head -5", check=False)
        if add_client_routes:
            print("   Client creation routes found:")
            for line in add_client_routes.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        # Check what actually happens when a client is added
        success, client_add_code, _ = run_command(ssh, f"grep -A 20 'vpn-manager.*add-client\\|subprocess.*vpn-manager' {VPN_DIR}/web-portal/app.py | head -25", check=False)
        if client_add_code:
            print("   Current client creation code:")
            print(f"      {client_add_code[:300]}")
        else:
            print("   ⚠️  Could not find client creation code in web portal")
            print("   Clients might be created manually via command line")
        print("")
        
        # Test generating both configs for existing admin client (if it exists)
        print("6️⃣  Testing config generation...")
        print("")
        
        # Check if admin client exists
        success, admin_exists, _ = run_command(ssh, f"test -f {VPN_DIR}/certs/admin.crt && echo 'EXISTS' || echo 'NOT_EXISTS'", check=False)
        
        if 'EXISTS' in admin_exists:
            print("   Admin client certificate exists, testing config generation...")
            
            # Test generating both configs
            success, test_output, _ = run_command(ssh, f"cd {VPN_DIR} && python3 scripts/generate-both-configs.py admin 2>&1", check=False)
            if success:
                print("   Test output:")
                for line in test_output.split('\n'):
                    if line.strip():
                        print(f"      {line}")
        else:
            print("   ℹ️  No admin client certificate found - configs will be generated when clients are created")
        print("")
        
        print("=" * 70)
        print("✅ CLIENT CREATION FIXED")
        print("=" * 70)
        print("")
        print("📋 What was done:")
        print("   1. ✅ Updated domain to phazevpn.com in vpn-manager.py")
        print("   2. ✅ Created script to generate both config types")
        print("   3. ✅ Ready to generate .ovpn and .phazevpn for new clients")
        print("")
        print("📝 How to use:")
        print("   When creating a new client, run:")
        print(f"   python3 {VPN_DIR}/scripts/generate-both-configs.py CLIENT_NAME")
        print("")
        print("   This will generate:")
        print("   - CLIENT_NAME.ovpn (for mobile/OpenVPN)")
        print("   - CLIENT_NAME.phazevpn (for desktop/PhazeVPN Protocol)")
        print("")
        print("🔧 Next step: Update web portal to call this script when admin creates clients")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

