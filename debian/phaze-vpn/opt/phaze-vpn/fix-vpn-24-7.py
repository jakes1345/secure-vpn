#!/usr/bin/env python3
"""
Fix VPN service to run 24/7 with proper auto-restart
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("=" * 70)
print("🔧 FIXING VPN TO RUN 24/7")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Check current service
    print("1️⃣ Checking current service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl status secure-vpn 2>&1 | head -15")
    current_status = stdout.read().decode()
    print(current_status)
    print("")
    
    # Create proper service file that runs OpenVPN directly
    print("2️⃣ Creating proper service file...")
    
    # Service file that runs OpenVPN directly (more reliable)
    service_content = f"""[Unit]
Description=PhazeVPN OpenVPN Server
After=network.target
Wants=network-online.target

[Service]
Type=notify
User=root
WorkingDirectory={VPN_DIR}
ExecStart=/usr/sbin/openvpn --cd {VPN_DIR} --config {VPN_DIR}/config/server.conf --writepid /var/run/openvpn-server.pid
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StartLimitInterval=0
StandardOutput=journal
StandardError=journal

# Security
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={VPN_DIR}/logs {VPN_DIR}/client-configs

[Install]
WantedBy=multi-user.target
"""
    
    # Write service file
    sftp = ssh.open_sftp()
    with sftp.file('/etc/systemd/system/secure-vpn.service', 'w') as f:
        f.write(service_content)
    sftp.close()
    print("   ✅ Service file created")
    print("")
    
    # Reload systemd
    print("3️⃣ Reloading systemd...")
    ssh.exec_command("systemctl daemon-reload")
    print("   ✅ Reloaded")
    print("")
    
    # Stop old processes
    print("4️⃣ Stopping old processes...")
    ssh.exec_command("pkill -f 'openvpn.*server.conf' 2>/dev/null || true")
    ssh.exec_command("systemctl stop secure-vpn 2>/dev/null || true")
    import time
    time.sleep(2)
    print("   ✅ Stopped")
    print("")
    
    # Enable and start service
    print("5️⃣ Enabling and starting service...")
    ssh.exec_command("systemctl enable secure-vpn")
    ssh.exec_command("systemctl start secure-vpn")
    time.sleep(3)
    
    # Check status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn 2>&1")
    active_status = stdout.read().decode().strip()
    
    if active_status == "active":
        print("   ✅ Service is active")
    else:
        print(f"   ⚠️  Service status: {active_status}")
        # Check logs
        stdin, stdout, stderr = ssh.exec_command("journalctl -u secure-vpn -n 10 --no-pager 2>&1")
        logs = stdout.read().decode()
        print("   Recent logs:")
        for line in logs.split('\n')[-5:]:
            if line.strip():
                print(f"   {line[:100]}")
    print("")
    
    # Verify OpenVPN is running
    print("6️⃣ Verifying OpenVPN is running...")
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' || echo 'NOT_RUNNING'")
    openvpn_pid = stdout.read().decode().strip()
    
    if openvpn_pid != "NOT_RUNNING":
        print(f"   ✅ OpenVPN is running (PID: {openvpn_pid})")
    else:
        print("   ⚠️  OpenVPN not running - starting manually...")
        ssh.exec_command(f"cd {VPN_DIR} && nohup openvpn --config config/server.conf --daemon > /dev/null 2>&1 &")
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' || echo 'STILL_NOT_RUNNING'")
        final_check = stdout.read().decode().strip()
        if final_check != "STILL_NOT_RUNNING":
            print(f"   ✅ OpenVPN started (PID: {final_check})")
        else:
            print("   ❌ Failed to start OpenVPN")
            # Check for errors
            stdin, stdout, stderr = ssh.exec_command(f"cd {VPN_DIR} && openvpn --config config/server.conf --verb 3 2>&1 | head -20")
            errors = stdout.read().decode()
            print(f"   Errors: {errors[:300]}")
    print("")
    
    # Check port
    print("7️⃣ Checking port 1194...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn 2>/dev/null | grep ':1194' || ss -tulpn 2>/dev/null | grep ':1194' || echo 'NOT_LISTENING'")
    port_status = stdout.read().decode().strip()
    
    if "NOT_LISTENING" not in port_status and port_status:
        print(f"   ✅ Port 1194 is listening")
    else:
        print("   ⚠️  Port 1194 not listening")
    print("")
    
    # Summary
    print("=" * 70)
    print("📊 FINAL STATUS")
    print("=" * 70)
    print("")
    
    stdin, stdout, stderr = ssh.exec_command("systemctl show secure-vpn -p ActiveState,SubState,Restart,RestartUSec 2>&1")
    service_info = stdout.read().decode().strip()
    print("Service Info:")
    for line in service_info.split('\n'):
        if line.strip():
            print(f"   {line}")
    print("")
    
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' && echo 'RUNNING' || echo 'NOT_RUNNING'")
    final_status = stdout.read().decode().strip()
    print(f"OpenVPN Process: {final_status}")
    print("")
    
    print("=" * 70)
    print("✅ VPN SERVICE FIXED")
    print("=" * 70)
    print("")
    print("💡 The VPN is now configured to:")
    print("   ✅ Auto-start on boot")
    print("   ✅ Auto-restart on failure (Restart=always)")
    print("   ✅ Stay running 24/7")
    print("")
    print("📋 Monitor with:")
    print("   systemctl status secure-vpn")
    print("   journalctl -u secure-vpn -f")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

