#!/usr/bin/env python3
from paramiko import SSHClient, AutoAddPolicy

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect("15.204.11.19", username="root", password="Jakes1328!@", timeout=10)

print("Restarting OpenVPN...")
ssh.exec_command("pkill -x openvpn; sleep 1; cd /opt/secure-vpn && openvpn --config config/server.conf --daemon")
time.sleep(2)

print("Restarting Web Portal...")
ssh.exec_command("pkill -f app.py; sleep 1; cd /opt/secure-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &")
time.sleep(2)

print("Checking status...")
stdin, stdout, stderr = ssh.exec_command("pgrep -x openvpn && echo 'OpenVPN: OK' || echo 'OpenVPN: FAIL'; pgrep -f app.py && echo 'Web Portal: OK' || echo 'Web Portal: FAIL'")
print(stdout.read().decode())

ssh.close()
print("Done!")

