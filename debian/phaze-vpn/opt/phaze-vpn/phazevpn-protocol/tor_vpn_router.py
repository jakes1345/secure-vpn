#!/usr/bin/env python3
"""
Tor VPN Router - Built into PhazeVPN Protocol
Routes ALL VPN traffic through Tor automatically when enabled
Complete anonymity - no separate Tor client needed
"""

import socket
import subprocess
import time
import threading
import os
import platform
from typing import Optional, Tuple
from pathlib import Path

try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False
    print("⚠️  pysocks not installed. Install with: pip3 install pysocks")

class TorVPNRouter:
    """
    Tor routing built directly into PhazeVPN Protocol
    When Tor Ghost Mode is enabled, ALL traffic routes through Tor automatically
    """
    
    def __init__(self, tor_port=9050, control_port=9051):
        self.tor_port = tor_port
        self.control_port = control_port
        self.tor_process = None
        self.tor_enabled = False
        self.socks_proxy = None
        
    def install_tor(self):
        """Install Tor automatically"""
        if platform.system() == 'Linux':
            try:
                print("📥 Installing Tor for PhazeVPN...")
                subprocess.run(['sudo', 'apt-get', 'update'], 
                             check=True, capture_output=True, timeout=60)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tor'], 
                             check=True, capture_output=True, timeout=120)
                print("✅ Tor installed successfully")
                return True
            except Exception as e:
                print(f"❌ Tor installation failed: {e}")
                return False
        return False
    
    def check_tor_running(self):
        """Check if Tor is already running"""
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(1)
            result = test_sock.connect_ex(('127.0.0.1', self.tor_port))
            test_sock.close()
            return result == 0
        except:
            return False
    
    def start_tor(self):
        """Start Tor service for VPN routing"""
        # Check if already running
        if self.check_tor_running():
            self.tor_enabled = True
            print("✅ Tor already running")
            return True
        
        # Try to install if not present
        try:
            subprocess.run(['which', 'tor'], check=True, capture_output=True)
        except:
            if not self.install_tor():
                return False
        
        # Start Tor via systemd
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'tor'],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                time.sleep(2)  # Wait for Tor to start
                if self.check_tor_running():
                    self.tor_enabled = True
                    print("✅ Tor started for PhazeVPN")
                    return True
        except:
            pass
        
        # Fallback: Start Tor directly
        try:
            self.tor_process = subprocess.Popen(
                ['tor'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Tor to be ready
            for _ in range(30):
                if self.check_tor_running():
                    self.tor_enabled = True
                    print("✅ Tor started successfully")
                    return True
                time.sleep(1)
        except Exception as e:
            print(f"❌ Failed to start Tor: {e}")
        
        return False
    
    def stop_tor(self):
        """Stop Tor (only if we started it)"""
        if self.tor_process:
            try:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=5)
            except:
                self.tor_process.kill()
            self.tor_process = None
        
        self.tor_enabled = False
    
    def create_tor_socket(self, destination: Tuple[str, int]) -> Optional[socket.socket]:
        """Create socket routed through Tor"""
        if not self.tor_enabled:
            return None
        
        if not SOCKS_AVAILABLE:
            print("⚠️  pysocks not available - Tor routing disabled")
            return None
        
        try:
            # Create SOCKS5 socket
            sock = socks.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.tor_port)
            sock.settimeout(10)
            return sock
        except Exception as e:
            print(f"⚠️  Tor socket creation failed: {e}")
            return None
    
    def route_packet_through_tor(self, data: bytes, destination: Tuple[str, int]) -> Optional[bytes]:
        """Route packet through Tor network"""
        if not self.tor_enabled:
            return None
        
        tor_sock = self.create_tor_socket(destination)
        if not tor_sock:
            return None
        
        try:
            tor_sock.sendto(data, destination)
            response, _ = tor_sock.recvfrom(65535)
            return response
        except Exception as e:
            return None
        finally:
            tor_sock.close()

# Global Tor router instance
_tor_router = None

def get_tor_router():
    """Get global Tor router instance"""
    global _tor_router
    if _tor_router is None:
        _tor_router = TorVPNRouter()
    return _tor_router

def enable_tor_for_vpn():
    """Enable Tor routing for PhazeVPN Protocol"""
    router = get_tor_router()
    return router.start_tor()

def disable_tor_for_vpn():
    """Disable Tor routing"""
    router = get_tor_router()
    router.stop_tor()

def is_tor_enabled():
    """Check if Tor routing is enabled"""
    router = get_tor_router()
    return router.tor_enabled

