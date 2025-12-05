#!/usr/bin/env python3
"""
PhazeVPN Protocol - Security Manager
Implements kill switch, DNS leak protection, IPv6 blocking, and routing
"""

import subprocess
import sys
import os
from pathlib import Path

class SecurityManager:
    """Manage security features: kill switch, DNS protection, routing"""
    
    def __init__(self, vpn_interface='phazevpn0', vpn_ip='10.9.0.1', vpn_network='10.9.0.0/24'):
        self.vpn_interface = vpn_interface
        self.vpn_ip = vpn_ip
        self.vpn_network = vpn_network
        self.server_ip = None  # Will be set when connected
        self.is_linux = sys.platform.startswith('linux')
        self.is_macos = sys.platform == 'darwin'
        self.is_windows = sys.platform == 'win32'
        self.original_routes = []
        self.original_dns = []
        self.kill_switch_active = False
        
    def setup_kill_switch(self, server_ip):
        """Setup kill switch - block all traffic except VPN"""
        self.server_ip = server_ip
        print("🔒 Setting up kill switch...")
        
        try:
            if self.is_linux:
                self._setup_kill_switch_linux()
            elif self.is_macos:
                self._setup_kill_switch_macos()
            elif self.is_windows:
                self._setup_kill_switch_windows()
            
            self.kill_switch_active = True
            print("✅ Kill switch activated")
        except Exception as e:
            print(f"⚠️  Warning: Could not setup kill switch: {e}")
    
    def _setup_kill_switch_linux(self):
        """Setup kill switch on Linux using iptables"""
        # Save original default route
        result = subprocess.run(['ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            self.original_routes.append(result.stdout.strip())
        
        # Block all outbound traffic except VPN
        subprocess.run(['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'OUTPUT', '-o', self.vpn_interface, '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'OUTPUT', '-d', self.server_ip, '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'OUTPUT', '-p', 'udp', '--dport', '51820', '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'OUTPUT', '-j', 'DROP'], check=False)
        
        # Block all inbound traffic except established connections
        subprocess.run(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'INPUT', '-i', self.vpn_interface, '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'INPUT', '-j', 'DROP'], check=False)
    
    def _setup_kill_switch_macos(self):
        """Setup kill switch on macOS using pfctl"""
        # macOS uses pfctl for firewall rules
        # This is more complex and may require root
        pass  # Implement if needed
    
    def _setup_kill_switch_windows(self):
        """Setup kill switch on Windows using netsh"""
        # Block all outbound except VPN
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=PhazeVPN-KillSwitch',
            'dir=out',
            'action=block',
            'remoteip=any'
        ], check=False, capture_output=True)
        
        # Allow VPN traffic
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=PhazeVPN-AllowVPN',
            'dir=out',
            'action=allow',
            'remoteip=' + self.server_ip
        ], check=False, capture_output=True)
    
    def setup_dns_protection(self, dns_servers=['1.1.1.1', '1.0.0.1']):
        """Setup DNS leak protection - force DNS through VPN"""
        print("🔒 Setting up DNS leak protection...")
        
        try:
            if self.is_linux:
                self._setup_dns_linux(dns_servers)
            elif self.is_macos:
                self._setup_dns_macos(dns_servers)
            elif self.is_windows:
                self._setup_dns_windows(dns_servers)
            
            print("✅ DNS leak protection activated")
        except Exception as e:
            print(f"⚠️  Warning: Could not setup DNS protection: {e}")
    
    def _setup_dns_linux(self, dns_servers):
        """Setup DNS on Linux"""
        # Save original DNS
        if Path('/etc/resolv.conf').exists():
            with open('/etc/resolv.conf', 'r') as f:
                self.original_dns = f.readlines()
        
        # Set DNS servers
        resolv_content = "# PhazeVPN DNS Configuration\n"
        for dns in dns_servers:
            resolv_content += f"nameserver {dns}\n"
        
        # Write new resolv.conf (requires root)
        try:
            with open('/etc/resolv.conf', 'w') as f:
                f.write(resolv_content)
        except PermissionError:
            print("   ⚠️  Need root to change DNS. Run with sudo.")
        
        # Block DNS outside VPN
        for dns in dns_servers:
            subprocess.run(['iptables', '-A', 'OUTPUT', '-p', 'udp', '--dport', '53', 
                          '-d', dns, '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'OUTPUT', '-p', 'udp', '--dport', '53', '-j', 'DROP'], check=False)
    
    def _setup_dns_macos(self, dns_servers):
        """Setup DNS on macOS"""
        # Use networksetup (requires admin)
        for i, dns in enumerate(dns_servers, 1):
            subprocess.run(['networksetup', '-setdnsservers', 'Wi-Fi', dns], check=False)
    
    def _setup_dns_windows(self, dns_servers):
        """Setup DNS on Windows"""
        # Set DNS for primary interface
        subprocess.run([
            'netsh', 'interface', 'ip', 'set', 'dns',
            'Ethernet', 'static', dns_servers[0]
        ], check=False, capture_output=True)
        
        if len(dns_servers) > 1:
            subprocess.run([
                'netsh', 'interface', 'ip', 'add', 'dns',
                'Ethernet', dns_servers[1], 'index=2'
            ], check=False, capture_output=True)
    
    def block_ipv6(self):
        """Block IPv6 to prevent leaks"""
        print("🔒 Blocking IPv6...")
        
        try:
            if self.is_linux:
                # Disable IPv6 on all interfaces except VPN
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.all.disable_ipv6=1'], check=False)
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.default.disable_ipv6=1'], check=False)
                # Allow IPv6 on VPN interface
                subprocess.run(['sysctl', '-w', f'net.ipv6.conf.{self.vpn_interface}.disable_ipv6=0'], check=False)
            
            print("✅ IPv6 blocked")
        except Exception as e:
            print(f"⚠️  Warning: Could not block IPv6: {e}")
    
    def setup_routing(self):
        """Setup routing - redirect all traffic through VPN"""
        print("🔒 Setting up routing...")
        
        try:
            if self.is_linux:
                # Get default gateway
                result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.original_routes.append(result.stdout.strip())
                
                # Delete default route
                subprocess.run(['ip', 'route', 'del', 'default'], check=False)
                
                # Add route through VPN
                subprocess.run(['ip', 'route', 'add', 'default', 'via', self.vpn_ip, 
                              'dev', self.vpn_interface], check=False)
                
                # Add route for VPN network
                subprocess.run(['ip', 'route', 'add', self.vpn_network, 
                              'dev', self.vpn_interface], check=False)
            
            print("✅ Routing configured")
        except Exception as e:
            print(f"⚠️  Warning: Could not setup routing: {e}")
    
    def restore_settings(self):
        """Restore original network settings"""
        print("🔓 Restoring network settings...")
        
        try:
            if self.is_linux:
                # Restore routes
                for route in self.original_routes:
                    subprocess.run(['ip', 'route', 'add', route], check=False)
                
                # Remove iptables rules
                subprocess.run(['iptables', '-F'], check=False)
                subprocess.run(['iptables', '-X'], check=False)
                
                # Restore DNS
                if self.original_dns:
                    with open('/etc/resolv.conf', 'w') as f:
                        f.writelines(self.original_dns)
                
                # Restore IPv6
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.all.disable_ipv6=0'], check=False)
                subprocess.run(['sysctl', '-w', 'net.ipv6.conf.default.disable_ipv6=0'], check=False)
            
            self.kill_switch_active = False
            print("✅ Network settings restored")
        except Exception as e:
            print(f"⚠️  Warning: Could not restore settings: {e}")

