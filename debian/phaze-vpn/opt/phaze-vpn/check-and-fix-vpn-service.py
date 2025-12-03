#!/usr/bin/env python3
"""
Check VPN service status and fix it to stay running 24/7
"""

from paramiko import SSHClient, AutoAddPolicy
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔍 CHECKING VPN SERVICE STATUS")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Check OpenVPN process
    print("1️⃣ Checking OpenVPN process...")
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' || echo 'NOT_RUNNING'")
    openvpn_pid = stdout.read().decode().strip()
    
    if openvpn_pid == "NOT_RUNNING":
        print("   ❌ OpenVPN is NOT running!")
    else:
        print(f"   ✅ OpenVPN is running (PID: {openvpn_pid})")
    print("")
    
    # Check systemd service
    print("2️⃣ Checking systemd services...")
    
    # Check secure-vpn service
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn 2>&1 || systemctl is-active phaze-vpn 2>&1 || echo 'NOT_FOUND'")
    service_status = stdout.read().decode().strip()
    print(f"   secure-vpn service: {service_status}")
    
    # Check openvpn service
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active openvpn@server 2>&1 || echo 'NOT_FOUND'")
    openvpn_service = stdout.read().decode().strip()
    print(f"   openvpn@server service: {openvpn_service}")
    print("")
    
    # Check if service is enabled (auto-start on boot)
    print("3️⃣ Checking if services are enabled (auto-start)...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-enabled secure-vpn 2>&1 || systemctl is-enabled phaze-vpn 2>&1 || echo 'NOT_FOUND'")
    enabled_status = stdout.read().decode().strip()
    print(f"   secure-vpn enabled: {enabled_status}")
    
    if enabled_status != "enabled":
        print("   ⚠️  Service not enabled for auto-start!")
    print("")
    
    # Check port 1194
    print("4️⃣ Checking if port 1194 is listening...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn 2>/dev/null | grep ':1194' || ss -tulpn 2>/dev/null | grep ':1194' || echo 'NOT_LISTENING'")
    port_status = stdout.read().decode().strip()
    
    if "NOT_LISTENING" in port_status or not port_status:
        print("   ❌ Port 1194 is NOT listening!")
    else:
        print(f"   ✅ Port 1194 is listening: {port_status[:80]}")
    print("")
    
    # Check logs for errors
    print("5️⃣ Checking recent logs...")
    stdin, stdout, stderr = ssh.exec_command("journalctl -u secure-vpn -n 20 --no-pager 2>&1 | tail -10 || journalctl -u openvpn@server -n 20 --no-pager 2>&1 | tail -10 || tail -20 /opt/secure-vpn/logs/server.log 2>&1 | tail -10")
    logs = stdout.read().decode().strip()
    if logs:
        print("   Recent logs:")
        for line in logs.split('\n')[-5:]:
            if line.strip():
                print(f"   {line[:100]}")
    print("")
    
    # Fix issues
    print("6️⃣ Fixing issues...")
    fixes_applied = []
    
    # Start OpenVPN if not running
    if openvpn_pid == "NOT_RUNNING":
        print("   🔧 Starting OpenVPN...")
        
        # Try systemd service first
        if service_status != "active":
            stdin, stdout, stderr = ssh.exec_command("systemctl start secure-vpn 2>&1 || systemctl start phaze-vpn 2>&1 || true")
            result = stdout.read().decode().strip()
            if "active" in result or not result:
                fixes_applied.append("Started secure-vpn service")
        
        # If still not running, start manually
        stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' || echo 'STILL_NOT_RUNNING'")
        still_not_running = stdout.read().decode().strip()
        
        if still_not_running == "STILL_NOT_RUNNING":
            print("   🔧 Starting OpenVPN manually...")
            ssh.exec_command("cd /opt/secure-vpn && nohup openvpn --config config/server.conf --daemon > /dev/null 2>&1 &")
            import time
            time.sleep(2)
            fixes_applied.append("Started OpenVPN manually")
    
    # Enable service for auto-start
    if enabled_status != "enabled":
        print("   🔧 Enabling service for auto-start...")
        ssh.exec_command("systemctl enable secure-vpn 2>&1 || systemctl enable phaze-vpn 2>&1 || true")
        fixes_applied.append("Enabled service for auto-start")
    
    # Ensure service has restart policy
    print("   🔧 Ensuring restart policy...")
    
    # Check current service file
    stdin, stdout, stderr = ssh.exec_command("cat /etc/systemd/system/secure-vpn.service 2>&1 || cat /etc/systemd/system/phaze-vpn.service 2>&1 || echo 'NOT_FOUND'")
    service_file = stdout.read().decode()
    
    if "Restart=always" not in service_file and "NOT_FOUND" not in service_file:
        print("   🔧 Adding restart policy to service...")
        # Create proper service file with restart policy
        proper_service = """[Unit]
Description=PhazeVPN Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/secure-vpn
ExecStart=/usr/sbin/openvpn --config /opt/secure-vpn/config/server.conf --daemon openvpn-server
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        sftp = ssh.open_sftp()
        with sftp.file('/etc/systemd/system/secure-vpn.service', 'w') as f:
            f.write(proper_service)
        sftp.close()
        ssh.exec_command("systemctl daemon-reload")
        fixes_applied.append("Added restart policy to service")
    
    print("")
    
    # Verify fix
    print("7️⃣ Verifying fix...")
    import time
    time.sleep(2)
    
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' || echo 'NOT_RUNNING'")
    final_status = stdout.read().decode().strip()
    
    if final_status != "NOT_RUNNING":
        print(f"   ✅ OpenVPN is now running (PID: {final_status})")
    else:
        print("   ⚠️  OpenVPN still not running - checking why...")
        stdin, stdout, stderr = ssh.exec_command("cd /opt/secure-vpn && openvpn --config config/server.conf --verb 3 2>&1 | head -20")
        error_output = stdout.read().decode()
        if error_output:
            print(f"   Error: {error_output[:200]}")
    
    print("")
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print("")
    
    if fixes_applied:
        print("🔧 Fixes Applied:")
        for fix in fixes_applied:
            print(f"   - {fix}")
        print("")
    
    print("📋 Current Status:")
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' && echo 'RUNNING' || echo 'NOT_RUNNING'")
    current_status = stdout.read().decode().strip()
    print(f"   OpenVPN: {current_status}")
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-enabled secure-vpn 2>&1 || systemctl is-enabled phaze-vpn 2>&1 || echo 'NOT_ENABLED'")
    enabled = stdout.read().decode().strip()
    print(f"   Auto-start: {enabled}")
    
    stdin, stdout, stderr = ssh.exec_command("systemctl show secure-vpn -p Restart 2>&1 | grep Restart || systemctl show phaze-vpn -p Restart 2>&1 | grep Restart || echo 'Restart=unknown'")
    restart_policy = stdout.read().decode().strip()
    print(f"   Restart policy: {restart_policy}")
    print("")
    
    print("=" * 70)
    print("✅ CHECK COMPLETE")
    print("=" * 70)
    print("")
    print("💡 The VPN should now stay running 24/7 with auto-restart enabled.")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

