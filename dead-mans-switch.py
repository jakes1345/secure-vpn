#!/usr/bin/env python3
"""
Dead Man's Switch for PhazeVPN
Automatically detects attacks and activates defensive measures
Like a game of pong - attacks bounce back at attackers
"""

import subprocess
import time
import json
import socket
import threading
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import psutil
import os

class DeadMansSwitch:
    def __init__(self):
        self.config_file = Path("/opt/phaze-vpn/dead-mans-switch.json")
        self.log_file = Path("/var/log/phazevpn-deadswitch.log")
        self.attack_threshold = 50  # Connections per minute
        self.response_time = 5  # Seconds to respond
        self.honeypot_active = False
        self.attackers = defaultdict(list)
        self.blocked_ips = set()
        self.honeypot_port = 8080  # Fake service port
        
        # Load config
        self.load_config()
        
    def load_config(self):
        """Load configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                    self.attack_threshold = config.get('attack_threshold', 50)
                    self.response_time = config.get('response_time', 5)
                    self.blocked_ips = set(config.get('blocked_ips', []))
            except:
                pass
    
    def save_config(self):
        """Save configuration"""
        config = {
            'attack_threshold': self.attack_threshold,
            'response_time': self.response_time,
            'blocked_ips': list(self.blocked_ips)
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def log(self, message):
        """Log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        print(log_msg.strip())
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_msg)
        except:
            pass
    
    def detect_attack(self):
        """Detect DDoS/attack patterns"""
        # Check network connections
        connections = psutil.net_connections(kind='inet')
        
        # Group by remote IP
        ip_connections = defaultdict(int)
        for conn in connections:
            if conn.status == 'ESTABLISHED' and conn.raddr:
                ip = conn.raddr.ip
                if ip not in ['127.0.0.1', '::1']:
                    ip_connections[ip] += 1
        
        # Detect suspicious patterns
        attackers = []
        for ip, count in ip_connections.items():
            if count > self.attack_threshold:
                attackers.append((ip, count))
                self.attackers[ip].append(datetime.now())
        
        # Clean old attack records (keep last hour)
        cutoff = datetime.now() - timedelta(hours=1)
        for ip in list(self.attackers.keys()):
            self.attackers[ip] = [t for t in self.attackers[ip] if t > cutoff]
            if not self.attackers[ip]:
                del self.attackers[ip]
        
        return attackers
    
    def block_ip(self, ip):
        """Block an IP address using iptables"""
        if ip in self.blocked_ips:
            return
        
        self.log(f"🚫 BLOCKING ATTACKER: {ip}")
        self.blocked_ips.add(ip)
        self.save_config()
        
        # Block with iptables
        try:
            subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], 
                         check=True, timeout=5)
            subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'REJECT', '--reject-with', 'icmp-port-unreachable'],
                         check=True, timeout=5)
            self.log(f"✅ IP {ip} blocked via iptables")
        except Exception as e:
            self.log(f"⚠️  Failed to block {ip}: {e}")
    
    def activate_honeypot(self, attacker_ip):
        """Activate honeypot to waste attacker resources"""
        if self.honeypot_active:
            return
        
        self.log(f"🍯 ACTIVATING HONEYPOT for {attacker_ip}")
        self.honeypot_active = True
        
        # Start honeypot server in background
        threading.Thread(target=self._run_honeypot, args=(attacker_ip,), daemon=True).start()
    
    def _run_honeypot(self, attacker_ip):
        """Run honeypot server that wastes attacker resources"""
        try:
            # Create fake service that responds slowly
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', self.honeypot_port))
            sock.listen(100)
            sock.settimeout(1)
            
            self.log(f"🍯 Honeypot active on port {self.honeypot_port}")
            
            connections = []
            start_time = time.time()
            
            # Run for 5 minutes or until stopped
            while time.time() - start_time < 300:
                try:
                    conn, addr = sock.accept()
                    if addr[0] == attacker_ip or True:  # Accept all connections
                        connections.append(conn)
                        # Send fake data slowly (waste their time)
                        threading.Thread(
                            target=self._waste_attacker_time,
                            args=(conn, addr),
                            daemon=True
                        ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    break
            
            # Close all connections
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass
            sock.close()
            
            self.honeypot_active = False
            self.log("🍯 Honeypot deactivated")
            
        except Exception as e:
            self.log(f"⚠️  Honeypot error: {e}")
            self.honeypot_active = False
    
    def _waste_attacker_time(self, conn, addr):
        """Waste attacker's time with slow responses"""
        try:
            # Send fake data very slowly
            fake_data = b"HTTP/1.1 200 OK\r\n" * 1000  # Large fake response
            chunk_size = 1  # Send 1 byte at a time (very slow)
            
            for i in range(0, len(fake_data), chunk_size):
                try:
                    conn.send(fake_data[i:i+chunk_size])
                    time.sleep(0.1)  # 100ms delay per byte (very slow)
                except:
                    break
            
            # Keep connection open as long as possible
            time.sleep(30)  # Keep connection for 30 seconds
            
        except:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def redirect_traffic(self, attacker_ip):
        """Redirect attacker traffic to honeypot (pong effect)"""
        self.log(f"🏓 REDIRECTING {attacker_ip} to honeypot (PONG!)")
        
        # Add iptables rule to redirect to honeypot
        try:
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-s', attacker_ip,
                '-p', 'tcp', '--dport', '80',
                '-j', 'REDIRECT', '--to-port', str(self.honeypot_port)
            ], check=True, timeout=5)
            self.log(f"✅ Traffic from {attacker_ip} redirected to honeypot")
        except Exception as e:
            self.log(f"⚠️  Redirect failed: {e}")
    
    def respond_to_attack(self, attackers):
        """Respond to detected attacks"""
        for ip, count in attackers:
            self.log(f"🚨 ATTACK DETECTED: {ip} ({count} connections)")
            
            # Immediate response: Block IP
            self.block_ip(ip)
            
            # Activate honeypot
            self.activate_honeypot(ip)
            
            # Redirect traffic (pong effect)
            self.redirect_traffic(ip)
            
            # Report attack
            self.report_attack(ip, count)
    
    def report_attack(self, ip, count):
        """Report attack (can be extended to notify admins)"""
        self.log(f"📊 ATTACK REPORT: IP {ip}, {count} connections")
        # Could send email, webhook, etc.
    
    def monitor(self):
        """Main monitoring loop"""
        self.log("🛡️  Dead Man's Switch ACTIVATED")
        self.log(f"   Attack threshold: {self.attack_threshold} connections/min")
        self.log(f"   Response time: {self.response_time} seconds")
        
        while True:
            try:
                # Detect attacks
                attackers = self.detect_attack()
                
                if attackers:
                    self.respond_to_attack(attackers)
                
                # Sleep before next check
                time.sleep(self.response_time)
                
            except KeyboardInterrupt:
                self.log("🛡️  Dead Man's Switch DEACTIVATED")
                break
            except Exception as e:
                self.log(f"⚠️  Monitor error: {e}")
                time.sleep(5)

def main():
    """Main entry point"""
    switch = DeadMansSwitch()
    switch.monitor()

if __name__ == '__main__':
    main()

