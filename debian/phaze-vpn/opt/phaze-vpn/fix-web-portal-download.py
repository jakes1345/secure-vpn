#!/usr/bin/env python3
"""
Fix web portal download - restart on correct port
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔧 FIXING WEB PORTAL DOWNLOAD")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected")
    print("")
    
    # Kill all app.py processes
    print("1️⃣ Stopping all web portal processes...")
    stdin, stdout, stderr = ssh.exec_command("pkill -9 -f 'app.py'; sleep 2; pgrep -f 'app.py' && echo 'Still running' || echo 'All stopped'")
    result = stdout.read().decode().strip()
    print(f"   {result}")
    print("")
    
    # Start web portal on port 8081
    print("2️⃣ Starting web portal on port 8081...")
    start_cmd = """cd /opt/secure-vpn/web-portal && nohup python3 app.py > /tmp/web-portal.log 2>&1 &"""
    stdin, stdout, stderr = ssh.exec_command(start_cmd)
    time.sleep(3)
    
    # Check if it started
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'app.py' && echo 'Running' || echo 'Not running'")
    status = stdout.read().decode().strip()
    print(f"   {status}")
    
    # Check port
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp | grep ':8081 ' && echo 'Port 8081 listening' || echo 'Port 8081 not listening'")
    port_status = stdout.read().decode().strip()
    print(f"   {port_status}")
    print("")
    
    # Test download route
    print("3️⃣ Testing download route...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -w '\\nHTTP:%{http_code}\\n' http://localhost:8081/download/client/windows 2>&1 | head -3")
    test_result = stdout.read().decode().strip()
    print(test_result)
    
    if "HTTP:200" in test_result or "#!/usr/bin/env python3" in test_result:
        print("   ✅ Download route working!")
    else:
        print("   ❌ Download route not working")
        # Check logs
        stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/web-portal.log 2>/dev/null || echo 'No logs'")
        logs = stdout.read().decode().strip()
        print(f"   Logs: {logs[:200]}")
    print("")
    
    print("=" * 60)
    print("✅ FIX COMPLETE")
    print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

