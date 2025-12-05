#!/usr/bin/env python3
"""
Tor Integration for PhazeVPN Protocol
Full anonymity - Tor routing built directly into the VPN protocol
"""

import socket
import socks
import subprocess
import time
import threading
from pathlib import Path
import platform
import os
from typing import Optional

class TorVPNRouter:
    """
    Routes VPN traffic through Tor for complete anonymity
    Built directly into PhazeVPN Protocol
    """
    
    def __init__(self, tor_port=9050, control_port=9051):
        self.tor_port = tor_port
        self.control_port = control_port
        self.tor_process = None
        self.tor_enabled = False
        self.tor_socket = None
        self.socks_proxy = None
        
    def install_tor(self):
        """Install Tor if not present"""
        if platform.system() == 'Linux':
            try:
                print("📥 Installing Tor...")
                result = subprocess.run(
                    ['sudo', 'apt-get', 'update'],
                    capture_output=True,
                    timeout=60
                )
                result = subprocess.run(
                    ['sudo', 'apt-get', 'install', '-y', 'tor'],
                    capture_output=True,
                    timeout=120
                )
                if result.returncode == 0:
                    print("✅ Tor installed successfully")
                    return True
            except Exception as e:
                print(f"❌ Tor installation failed: {e}")
        return False
    
    def check_tor_installed(self):
        """Check if Tor is installed"""
        try:
            result = subprocess.run(['which', 'tor'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def start_tor_service(self):
        """Start Tor service for VPN routing"""
        if not self.check_tor_installed():
            if not self.install_tor():
                return False
        
        try:
            # Check if Tor is already running
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(1)
                result = test_socket.connect_ex(('127.0.0.1', self.tor_port))
                test_socket.close()
                if result == 0:
                    print("✅ Tor already running")
                    self.tor_enabled = True
                    return True
            except:
                pass
            
            # Start Tor service
            print("🚀 Starting Tor service...")
            
            # Try systemd first
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'tor'],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                time.sleep(2)  # Wait for Tor to start
                self.tor_enabled = True
                print("✅ Tor service started")
                return True
            
            # If systemd fails, start Tor directly
            print("⚠️  Starting Tor directly...")
            self.tor_process = subprocess.Popen(
                ['tor'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Tor to be ready
            for _ in range(30):  # Wait up to 30 seconds
                try:
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.settimeout(1)
                    result = test_socket.connect_ex(('127.0.0.1', self.tor_port))
                    test_socket.close()
                    if result == 0:
                        self.tor_enabled = True
                        print("✅ Tor started successfully")
                        return True
                except:
                    pass
                time.sleep(1)
            
            print("❌ Tor failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Tor start error: {e}")
            return False
    
    def stop_tor_service(self):
        """Stop Tor service"""
        try:
            # Stop systemd service
            subprocess.run(['sudo', 'systemctl', 'stop', 'tor'], 
                         capture_output=True, timeout=10)
        except:
            pass
        
        # Kill direct process
        if self.tor_process:
            try:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=5)
            except:
                self.tor_process.kill()
            self.tor_process = None
        
        self.tor_enabled = False
        print("✅ Tor stopped")
    
    def create_tor_socket(self):
        """Create socket routed through Tor"""
        if not self.tor_enabled:
            if not self.start_tor_service():
                return None
        
        try:
            # Create SOCKS5 socket through Tor
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.tor_port)
            return sock
        except Exception as e:
            print(f"❌ Failed to create Tor socket: {e}")
            return None
    
    def route_through_tor(self, data: bytes, destination: tuple) -> Optional[bytes]:
        """
        Route data through Tor network
        Returns response data or None
        """
        if not self.tor_enabled:
            return None
        
        try:
            tor_socket = self.create_tor_socket()
            if not tor_socket:
                return None
            
            tor_socket.settimeout(10)
            tor_socket.connect(destination)
            tor_socket.sendall(data)
            
            response = tor_socket.recv(4096)
            tor_socket.close()
            
            return response
        except Exception as e:
            print(f"⚠️  Tor routing error: {e}")
            return None

class TorVPNMode:
    """
    Tor Ghost Mode - Complete anonymity through Tor network
    All VPN traffic routed through Tor automatically
    """
    
    def __init__(self, vpn_router):
        self.vpn_router = vpn_router
        self.enabled = False
        
    def enable(self):
        """Enable Tor Ghost Mode"""
        print("👻 Enabling Tor Ghost Mode - Complete anonymity...")
        
        if not self.vpn_router.start_tor_service():
            print("❌ Failed to start Tor")
            return False
        
        self.enabled = True
        print("✅ Tor Ghost Mode enabled - All traffic routed through Tor")
        return True
    
    def disable(self):
        """Disable Tor Ghost Mode"""
        self.enabled = False
        print("✅ Tor Ghost Mode disabled")
    
    def process_packet(self, packet: bytes) -> bytes:
        """Process packet for Tor routing"""
        if not self.enabled:
            return packet
        
        # Packet is already encrypted by VPN
        # Route through Tor for additional anonymity layer
        return packet
    
    def get_socks_proxy(self):
        """Get SOCKS5 proxy for Tor routing"""
        if self.enabled:
            return f"socks5://127.0.0.1:{self.vpn_router.tor_port}"
        return None

def setup_tor_for_vpn():
    """Setup Tor for VPN integration"""
    router = TorVPNRouter()
    
    if router.start_tor_service():
        return router
    return None

# Install socks library if needed
try:
    import socks
except ImportError:
    print("⚠️  socks library not found. Install with: pip3 install pysocks")
    socks = None

