#!/usr/bin/env python3
"""
Diagnose Portal Issue - Find what's actually wrong
"""

import paramiko
import time

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
    print("🔍 Diagnosing Portal Issue...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Check if portal service is running
        print("1️⃣ Checking Portal Service...")
        success, output, error = run_command(
            ssh,
            "systemctl status phazevpn-portal --no-pager | head -10",
            check=False
        )
        print(output)
        
        # 2. Check if portal is listening on port 8080
        print("\n2️⃣ Checking Port 8080...")
        success, output, error = run_command(
            ssh,
            "ss -tlnp | grep ':8080'",
            check=False
        )
        print(f"Port 8080: {output if output else 'NOT LISTENING'}")
        
        # 3. Check Nginx status
        print("\n3️⃣ Checking Nginx Status...")
        success, output, error = run_command(
            ssh,
            "systemctl status nginx --no-pager | head -10",
            check=False
        )
        print(output)
        
        # 4. Check Nginx configs
        print("\n4️⃣ Checking Nginx Configs...")
        success, output, error = run_command(
            ssh,
            "ls -la /etc/nginx/sites-enabled/",
            check=False
        )
        print(output)
        
        # 5. Check what Nginx is actually serving
        print("\n5️⃣ Testing Nginx Routing...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | head -20",
            check=False
        )
        print(f"Mail subdomain response:\n{output[:500]}")
        
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: phazevpn.duckdns.org' http://localhost/ | head -20",
            check=False
        )
        print(f"\nMain domain response:\n{output[:500]}")
        
        # 6. Check if portal app is actually running
        print("\n6️⃣ Checking Portal Process...")
        success, output, error = run_command(
            ssh,
            "ps aux | grep -E 'python.*portal|python.*8080' | grep -v grep",
            check=False
        )
        print(f"Portal processes: {output if output else 'NONE FOUND'}")
        
        # 7. Check portal logs
        print("\n7️⃣ Checking Portal Logs (last 20 lines)...")
        success, output, error = run_command(
            ssh,
            "journalctl -u phazevpn-portal -n 20 --no-pager",
            check=False
        )
        print(output)
        
        # 8. Try to start portal if not running
        print("\n8️⃣ Attempting to Start Portal...")
        success, output, error = run_command(
            ssh,
            "systemctl start phazevpn-portal && sleep 2 && systemctl status phazevpn-portal --no-pager | head -5",
            check=False
        )
        print(output)
        
        # 9. Test direct connection to portal
        print("\n9️⃣ Testing Direct Portal Connection...")
        success, output, error = run_command(
            ssh,
            "curl -s http://127.0.0.1:8080/ | head -10",
            check=False
        )
        print(f"Direct portal (127.0.0.1:8080):\n{output[:300]}")
        
        # 10. Check firewall
        print("\n🔟 Checking Firewall...")
        success, output, error = run_command(
            ssh,
            "ufw status | grep -E '80|8080'",
            check=False
        )
        print(f"Firewall rules: {output if output else 'NO RULES FOUND'}")
        
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
