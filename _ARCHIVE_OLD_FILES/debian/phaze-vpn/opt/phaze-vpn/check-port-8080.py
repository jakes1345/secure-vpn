#!/usr/bin/env python3
"""
Check Port 8080 - See what's actually running
"""

import paramiko

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def main():
    print("🔍 Checking Port 8080...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. What's listening on 8080?
        print("1️⃣ What's listening on port 8080?")
        success, output, error = run_command(
            ssh,
            "ss -tlnp | grep ':8080'",
            check=False
        )
        print(f"   {output}")
        
        # 2. What process is it?
        print("\n2️⃣ Process details...")
        success, output, error = run_command(
            ssh,
            "ps aux | grep -E 'gunicorn.*8080|python.*8080' | grep -v grep",
            check=False
        )
        print(f"   {output}")
        
        # 3. Check systemd services
        print("\n3️⃣ Systemd services...")
        success, output, error = run_command(
            ssh,
            "systemctl list-units --type=service | grep -E 'portal|8080'",
            check=False
        )
        print(f"   {output}")
        
        # 4. Check what unified portal service is doing
        print("\n4️⃣ Unified portal service status...")
        success, output, error = run_command(
            ssh,
            "systemctl status phazevpn-unified-portal --no-pager | head -20",
            check=False
        )
        print(output)
        
        # 5. Check VPN portal service
        print("\n5️⃣ VPN portal service status...")
        success, output, error = run_command(
            ssh,
            "systemctl status phazevpn-portal --no-pager | head -20",
            check=False
        )
        print(output)
        
        # 6. Test direct connection to 8080
        print("\n6️⃣ Direct test to 127.0.0.1:8080...")
        success, output, error = run_command(
            ssh,
            "curl -s http://127.0.0.1:8080/ | head -30",
            check=False
        )
        print(f"   Response preview:\n{output[:500]}")
        
        # 7. Check working directory of processes
        print("\n7️⃣ Working directories...")
        success, output, error = run_command(
            ssh,
            "for pid in $(pgrep -f 'gunicorn.*8080'); do echo \"PID $pid:\"; pwdx $pid 2>/dev/null || ls -la /proc/$pid/cwd 2>/dev/null | grep -o '/.*'; done",
            check=False
        )
        print(f"   {output}")
        
        print("\n" + "="*50)
        print("DIAGNOSIS COMPLETE")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

