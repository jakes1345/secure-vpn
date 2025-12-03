#!/usr/bin/env python3
"""
Fix External Access - Make site accessible to friends
Check firewall, nginx, and network configuration
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔍 DIAGNOSING EXTERNAL ACCESS ISSUES")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print()
    
    # Step 1: Check firewall status
    print("1️⃣ Checking firewall (UFW)...")
    stdin, stdout, stderr = ssh.exec_command("ufw status verbose 2>&1")
    ufw_status = stdout.read().decode()
    print(ufw_status)
    
    # Check if ports 80 and 443 are allowed
    if "80/tcp" not in ufw_status or "443/tcp" not in ufw_status:
        print("   ⚠️  Ports 80/443 not in firewall rules")
    else:
        print("   ✅ Ports 80/443 are allowed")
    print()
    
    # Step 2: Check nginx configuration
    print("2️⃣ Checking nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("grep -r 'listen' /etc/nginx/sites-enabled/ 2>&1 | head -10")
    nginx_listen = stdout.read().decode()
    print(nginx_listen)
    
    # Check if nginx is listening on all interfaces
    if "0.0.0.0" not in nginx_listen and "::" not in nginx_listen:
        print("   ⚠️  Nginx might only be listening on localhost")
    else:
        print("   ✅ Nginx listening on all interfaces")
    print()
    
    # Step 3: Check what ports are actually listening
    print("3️⃣ Checking listening ports...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln 2>/dev/null | grep -E ':(80|443)' || ss -tulpn 2>/dev/null | grep -E ':(80|443)'")
    listening_ports = stdout.read().decode()
    print(listening_ports)
    if listening_ports:
        if "0.0.0.0" in listening_ports or "::" in listening_ports:
            print("   ✅ Ports 80/443 listening on all interfaces")
        else:
            print("   ⚠️  Ports might only be listening on localhost")
    else:
        print("   ❌ Ports 80/443 not listening!")
    print()
    
    # Step 4: Check iptables rules
    print("4️⃣ Checking iptables rules...")
    stdin, stdout, stderr = ssh.exec_command("iptables -L -n -v | grep -E '(80|443|ACCEPT|DROP)' | head -20")
    iptables = stdout.read().decode()
    if iptables:
        print(iptables)
    else:
        print("   (No specific iptables rules found)")
    print()
    
    # Step 5: Check if there's a cloud firewall (OVH, etc.)
    print("5️⃣ Checking for cloud firewall...")
    stdin, stdout, stderr = ssh.exec_command("hostname -I")
    server_ips = stdout.read().decode().strip()
    print(f"   Server IPs: {server_ips}")
    print("   ⚠️  If using OVH/cloud provider, check their firewall panel!")
    print()
    
    # Step 6: Test external access from server
    print("6️⃣ Testing external access...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://15.204.11.19/ 2>&1")
    external_test = stdout.read().decode().strip()
    print(f"   External IP test: {external_test}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://phazevpn.duckdns.org/ 2>&1")
    domain_test = stdout.read().decode().strip()
    print(f"   Domain test: {domain_test}")
    print()
    
    # Now fix issues
    print("=" * 70)
    print("🔧 FIXING EXTERNAL ACCESS")
    print("=" * 70)
    print()
    
    # Fix 1: Ensure UFW allows HTTP/HTTPS
    print("1️⃣ Configuring firewall...")
    ssh.exec_command("ufw allow 80/tcp 2>&1")
    ssh.exec_command("ufw allow 443/tcp 2>&1")
    ssh.exec_command("ufw --force enable 2>&1")
    print("   ✅ Firewall configured")
    print()
    
    # Fix 2: Check nginx server block
    print("2️⃣ Checking nginx server block...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/default 2>&1 | head -30")
    nginx_config = stdout.read().decode()
    print(nginx_config)
    
    # Make sure nginx listens on all interfaces
    if "listen 80" not in nginx_config and "listen [::]:80" not in nginx_config:
        print("   ⚠️  Nginx might need configuration update")
    print()
    
    # Fix 3: Restart nginx
    print("3️⃣ Restarting nginx...")
    ssh.exec_command("systemctl restart nginx 2>&1")
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx 2>&1")
    nginx_status = stdout.read().decode().strip()
    print(f"   Nginx status: {nginx_status}")
    print()
    
    # Fix 4: Check if there are any other firewalls
    print("4️⃣ Checking for other firewalls...")
    stdin, stdout, stderr = ssh.exec_command("which firewalld && systemctl status firewalld 2>&1 | head -5 || echo 'firewalld not found'")
    firewalld = stdout.read().decode()
    print(firewalld)
    print()
    
    # Final verification
    print("=" * 70)
    print("📊 FINAL STATUS")
    print("=" * 70)
    print()
    
    # Check firewall again
    stdin, stdout, stderr = ssh.exec_command("ufw status | grep -E '(80|443)'")
    ufw_final = stdout.read().decode()
    if ufw_final:
        print("✅ Firewall rules:")
        print(ufw_final)
    else:
        print("⚠️  Firewall rules not found")
    
    # Check listening ports
    stdin, stdout, stderr = ssh.exec_command("ss -tulpn | grep -E ':(80|443)'")
    ports_final = stdout.read().decode()
    if ports_final:
        print("✅ Listening ports:")
        print(ports_final)
    
    print()
    print("🌐 Access URLs:")
    print(f"   http://{VPS_IP}")
    print("   https://phazevpn.duckdns.org")
    print()
    print("⚠️  IMPORTANT: If still not accessible:")
    print("   1. Check OVH/cloud provider firewall panel")
    print("   2. Ensure ports 80/443 are open in cloud firewall")
    print("   3. Check if domain DNS is pointing to correct IP")
    print("   4. Try accessing via IP first: http://15.204.11.19")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

