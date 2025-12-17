#!/usr/bin/env python3
"""
Test download route on VPS
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🧪 TESTING DOWNLOAD ROUTE")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Test 1: Check if client file exists
    print("1️⃣ Checking client file...")
    stdin, stdout, stderr = ssh.exec_command("test -f /opt/secure-vpn/phazevpn-client/phazevpn-client.py && echo 'EXISTS' || echo 'NOT FOUND'")
    file_check = stdout.read().decode().strip()
    print(f"   {file_check}")
    if file_check == "EXISTS":
        stdin, stdout, stderr = ssh.exec_command("ls -lh /opt/secure-vpn/phazevpn-client/phazevpn-client.py")
        file_info = stdout.read().decode().strip()
        print(f"   {file_info}")
    print("")
    
    # Test 2: Check VPN_DIR path resolution
    print("2️⃣ Testing path resolution in Python...")
    test_script = """
from pathlib import Path
VPN_DIR = Path('/opt/secure-vpn')
client_file = VPN_DIR / 'phazevpn-client' / 'phazevpn-client.py'
print(f'VPN_DIR: {VPN_DIR}')
print(f'Client path: {client_file}')
print(f'Exists: {client_file.exists()}')
"""
    stdin, stdout, stderr = ssh.exec_command(f"cd /opt/secure-vpn/web-portal && python3 -c \"{test_script}\"")
    path_test = stdout.read().decode().strip()
    print(path_test)
    print("")
    
    # Test 3: Test download route with GET request
    print("3️⃣ Testing download route...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -w '\\nHTTP_CODE:%{http_code}\\n' http://localhost:8081/download/client/windows 2>&1 | head -20")
    download_test = stdout.read().decode().strip()
    print(download_test)
    print("")
    
    # Test 4: Check web portal process
    print("4️⃣ Checking web portal process...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'app.py' | grep -v grep")
    process_info = stdout.read().decode().strip()
    if process_info:
        print(f"   ✅ {process_info}")
    else:
        print("   ❌ Web portal not running!")
    print("")
    
    # Test 5: Check if port 8081 is listening
    print("5️⃣ Checking port 8081...")
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp | grep ':8081 ' || echo 'NOT LISTENING'")
    port_check = stdout.read().decode().strip()
    print(f"   {port_check}")
    print("")
    
    print("=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

