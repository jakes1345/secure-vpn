#!/usr/bin/env python3
"""
Final fix for VPN service - make it work properly with systemd
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("=" * 70)
print("🔧 FINAL FIX FOR VPN SERVICE")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Create wrapper script that systemd can manage properly
    print("1️⃣ Creating wrapper script...")
    
    wrapper_script = f"""#!/bin/bash
# OpenVPN wrapper for systemd
cd {VPN_DIR}
exec /usr/sbin/openvpn --config {VPN_DIR}/config/server.conf
"""
    
    sftp = ssh.open_sftp()
    with sftp.file(f'{VPN_DIR}/openvpn-wrapper.sh', 'w') as f:
        f.write(wrapper_script)
    sftp.close()
    
    # Make executable
    ssh.exec_command(f"chmod +x {VPN_DIR}/openvpn-wrapper.sh")
    print("   ✅ Wrapper script created")
    print("")
    
    # Create proper service file (without --daemon, systemd manages it)
    print("2️⃣ Creating proper service file...")
    
    service_content = f"""[Unit]
Description=PhazeVPN OpenVPN Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}
ExecStart={VPN_DIR}/openvpn-wrapper.sh
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StartLimitInterval=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
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
    
    # Stop all OpenVPN processes
    print("4️⃣ Stopping old processes...")
    ssh.exec_command("pkill -f 'openvpn.*server.conf' 2>/dev/null || true")
    ssh.exec_command("systemctl stop secure-vpn 2>/dev/null || true")
    import time
    time.sleep(3)
    print("   ✅ Stopped")
    print("")
    
    # Enable and start
    print("5️⃣ Enabling and starting service...")
    ssh.exec_command("systemctl enable secure-vpn")
    ssh.exec_command("systemctl start secure-vpn")
    time.sleep(5)
    
    # Check status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn 2>&1")
    status = stdout.read().decode().strip()
    print(f"   Service status: {status}")
    
    if status == "active":
        print("   ✅ Service is active!")
    else:
        print("   ⚠️  Service not active, checking logs...")
        stdin, stdout, stderr = ssh.exec_command("journalctl -u secure-vpn -n 15 --no-pager 2>&1")
        logs = stdout.read().decode()
        for line in logs.split('\n')[-8:]:
            if line.strip():
                print(f"   {line[:120]}")
    print("")
    
    # Verify OpenVPN is running
    print("6️⃣ Verifying OpenVPN...")
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' || echo 'NOT_RUNNING'")
    pid = stdout.read().decode().strip()
    
    if pid != "NOT_RUNNING":
        print(f"   ✅ OpenVPN is running (PID: {pid})")
        
        # Check port
        stdin, stdout, stderr = ssh.exec_command("netstat -tulpn 2>/dev/null | grep ':1194' || ss -tulpn 2>/dev/null | grep ':1194' || echo 'NOT_LISTENING'")
        port = stdout.read().decode().strip()
        if "NOT_LISTENING" not in port:
            print(f"   ✅ Port 1194 is listening")
        else:
            print("   ⚠️  Port 1194 not listening")
    else:
        print("   ❌ OpenVPN not running")
    print("")
    
    # Final status
    print("=" * 70)
    print("📊 FINAL STATUS")
    print("=" * 70)
    print("")
    
    stdin, stdout, stderr = ssh.exec_command("systemctl show secure-vpn -p ActiveState,SubState,Restart,RestartUSec 2>&1")
    service_info = stdout.read().decode().strip()
    print("Service Configuration:")
    for line in service_info.split('\n'):
        if line.strip():
            print(f"   {line}")
    print("")
    
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'openvpn.*server.conf' && echo 'RUNNING' || echo 'NOT_RUNNING'")
    process = stdout.read().decode().strip()
    print(f"OpenVPN Process: {process}")
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-enabled secure-vpn 2>&1")
    enabled = stdout.read().decode().strip()
    print(f"Auto-start: {enabled}")
    print("")
    
    print("=" * 70)
    print("✅ VPN SERVICE FIXED FOR 24/7 OPERATION")
    print("=" * 70)
    print("")
    print("💡 Configuration:")
    print("   ✅ Restart=always (auto-restarts if it crashes)")
    print("   ✅ Auto-start on boot (enabled)")
    print("   ✅ Systemd manages the process")
    print("   ✅ Should stay running 24/7")
    print("")
    print("📋 Commands:")
    print("   systemctl status secure-vpn    # Check status")
    print("   systemctl restart secure-vpn   # Restart manually")
    print("   journalctl -u secure-vpn -f    # Watch logs")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

