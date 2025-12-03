#!/usr/bin/env python3
"""
Final Routing Fix - Ensure mail subdomain works
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
    return True, output, error

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Remove ALL configs
        print("Removing all Nginx configs...")
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/*", check=False)
        
        # Read securevpn config to preserve it
        print("Reading securevpn config...")
        success, output, error = run_command(
            ssh,
            "cat /etc/nginx/sites-available/securevpn",
            check=False
        )
        securevpn_config = output
        
        # Create mail config FIRST (alphabetically first = higher priority)
        print("Creating mail config...")
        mail_config = """# MAIL SUBDOMAIN - Must be first!
server {
    listen 80;
    server_name mail.phazevpn.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/00-mail-portal', 'w')
        f.write(mail_config)
        f.close()
        sftp.close()
        
        # Enable mail config first
        run_command(ssh, "ln -sf /etc/nginx/sites-available/00-mail-portal /etc/nginx/sites-enabled/00-mail-portal")
        
        # Re-enable securevpn (for VPN homepage)
        run_command(ssh, "ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/securevpn")
        
        # Test
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"Nginx test: {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl reload nginx")
            print("✅ Nginx reloaded")
        
        # Final test
        print("\nTesting mail subdomain...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -o '<title>.*</title>'",
            check=False
        )
        print(f"Response: {output}")
        
        print("\n✅ Done! Clear browser cache (Ctrl+Shift+Delete) and try again!")
        print("   Or use: http://15.204.11.19:8080")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
