#!/usr/bin/env python3
"""
Fix Nginx Error
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
        # Check nginx error
        print("Checking Nginx error...")
        success, output, error = run_command(
            ssh,
            "nginx -t 2>&1",
            check=False
        )
        print(output)
        print(error)
        
        # Check if cert exists
        success, output, error = run_command(
            ssh,
            "ls -la /etc/letsencrypt/live/mail.phazevpn.duckdns.org/ 2>&1 || echo 'CERT NOT FOUND'",
            check=False
        )
        print(f"\nCertificate check: {output}")
        
        # Simple HTTP config that definitely works
        print("\nCreating simple HTTP config...")
        simple_config = """server {
    listen 80;
    server_name mail.phazevpn.duckdns.org _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/phazevpn-portal', 'w')
        f.write(simple_config)
        f.close()
        sftp.close()
        
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/phazevpn-portal*")
        run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-portal /etc/nginx/sites-enabled/")
        
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"\nNginx test: {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl restart nginx")
            print("\n✅ Nginx fixed!")
        else:
            print(f"\n⚠️  Still has issues: {error}")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
