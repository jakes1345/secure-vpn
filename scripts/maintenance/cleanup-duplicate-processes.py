#!/usr/bin/env python3
"""
Clean up duplicate Flask processes and ensure only systemd service runs
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🧹 CLEANING UP DUPLICATE PROCESSES")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Get all Flask processes
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'app.py'")
    pids = stdout.read().decode().strip().split('\n')
    pids = [p for p in pids if p]
    
    print(f"Found {len(pids)} Flask process(es)")
    
    if len(pids) > 1:
        print("   ⚠️  Multiple processes detected, cleaning up...")
        
        # Get the systemd service PID
        stdin, stdout, stderr = ssh.exec_command("systemctl show phazevpn-web -p MainPID --value 2>&1")
        service_pid = stdout.read().decode().strip()
        
        if service_pid and service_pid.isdigit():
            service_pid = int(service_pid)
            print(f"   Systemd service PID: {service_pid}")
            
            # Kill all except the systemd one
            for pid in pids:
                pid_int = int(pid)
                if pid_int != service_pid:
                    print(f"   🗑️  Killing duplicate process: {pid_int}")
                    ssh.exec_command(f"kill {pid_int} 2>/dev/null")
        else:
            # No systemd service, keep one and kill others
            print(f"   🗑️  Killing all except first process")
            for pid in pids[1:]:
                ssh.exec_command(f"kill {pid} 2>/dev/null")
        
        import time
        time.sleep(2)
        
        # Verify
        stdin, stdout, stderr = ssh.exec_command("pgrep -f 'app.py' | wc -l")
        remaining = int(stdout.read().decode().strip())
        print(f"   ✅ Remaining processes: {remaining}")
    else:
        print("   ✅ Only one process running (good)")
    
    # Ensure systemd service is running
    print("")
    print("🔄 Ensuring systemd service is running...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    status = stdout.read().decode().strip()
    
    if status != "active":
        print("   Starting service...")
        ssh.exec_command("systemctl start phazevpn-web")
        import time
        time.sleep(2)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    final_status = stdout.read().decode().strip()
    print(f"   Service status: {final_status} {'✅' if final_status == 'active' else '❌'}")
    
    print("")
    print("=" * 70)
    print("✅ CLEANUP COMPLETE")
    print("=" * 70)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

