#!/usr/bin/env python3
"""
Fix SecureVPN Config - Remove mail subdomain from it
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
    print("🔧 Fixing SecureVPN Config...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Read securevpn config
        print("1️⃣ Reading securevpn config...")
        success, output, error = run_command(
            ssh,
            "cat /etc/nginx/sites-available/securevpn",
            check=False
        )
        print(f"Current config:\n{output[:500]}")
        
        # 2. Check if mail subdomain is in there
        if "mail.phazevpn.duckdns.org" in output:
            print("\n2️⃣ Found mail subdomain in securevpn config! Removing it...")
            
            # Read full config
            sftp = ssh.open_sftp()
            f = sftp.file('/etc/nginx/sites-available/securevpn', 'r')
            config = f.read().decode('utf-8')
            f.close()
            
            # Remove mail subdomain from server_name
            lines = config.split('\n')
            new_lines = []
            for line in lines:
                if 'server_name' in line and 'mail.phazevpn.duckdns.org' in line:
                    # Remove mail subdomain, keep only main domain
                    new_line = line.replace(' mail.phazevpn.duckdns.org', '').replace('mail.phazevpn.duckdns.org ', '').replace('mail.phazevpn.duckdns.org', '')
                    new_lines.append(new_line)
                    print(f"   Fixed: {line.strip()} -> {new_line.strip()}")
                else:
                    new_lines.append(line)
            
            # Write back
            f = sftp.file('/etc/nginx/sites-available/securevpn', 'w')
            f.write('\n'.join(new_lines))
            f.close()
            sftp.close()
            
            print("   ✅ Config updated")
        else:
            print("\n2️⃣ Mail subdomain not in securevpn config")
        
        # 3. Verify mail config is first
        print("\n3️⃣ Ensuring mail config is first...")
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/*", check=False)
        run_command(ssh, "ln -sf /etc/nginx/sites-available/00-mail-portal /etc/nginx/sites-enabled/00-mail-portal")
        run_command(ssh, "ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/securevpn")
        
        # 4. Test Nginx
        print("\n4️⃣ Testing Nginx...")
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"   {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx reloaded")
        
        # 5. Final test
        print("\n5️⃣ Final routing test...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -o '<title>.*</title>'",
            check=False
        )
        print(f"   Mail subdomain: {output}")
        
        if "Dashboard" in output or "PhazeVPN Platform" in output:
            print("   ✅ SUCCESS! Mail subdomain routing correctly!")
        else:
            print("   ⚠️  Still not working - checking all server_name directives...")
            success, output, error = run_command(
                ssh,
                "grep -r 'server_name' /etc/nginx/sites-enabled/",
                check=False
            )
            print(f"   All server_name directives:\n{output}")
        
        print("\n" + "="*50)
        print("✅ CONFIG FIXED!")
        print("="*50)
        print("\n🌐 Try: http://mail.phazevpn.duckdns.org")
        print("   Or: http://15.204.11.19:8080")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

