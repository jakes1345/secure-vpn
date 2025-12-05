#!/usr/bin/env python3
"""
PhazeVPN Protocol - TUN Interface Manager
Manages virtual network interface for VPN tunneling
"""

import os
import sys
import subprocess
import struct
import socket
from pathlib import Path

class TUNManager:
    """Manage TUN interface for VPN"""
    
    def __init__(self, interface_name='phazevpn0', ip_address='10.9.0.1', netmask='255.255.255.0'):
        self.interface_name = interface_name
        self.ip_address = ip_address
        self.netmask = netmask
        self.tun_fd = None
        self.is_windows = sys.platform == 'win32'
        self.is_linux = sys.platform.startswith('linux')
        self.is_macos = sys.platform == 'darwin'
    
    def create_tun(self):
        """Create TUN interface"""
        if self.is_linux:
            return self._create_tun_linux()
        elif self.is_macos:
            return self._create_tun_macos()
        elif self.is_windows:
            return self._create_tun_windows()
        else:
            raise OSError(f"Unsupported platform: {sys.platform}")
    
    def _create_tun_linux(self):
        """Create TUN interface on Linux"""
        try:
            import fcntl
            import ctypes
            
            TUNSETIFF = 0x400454ca
            IFF_TUN = 0x0001
            IFF_NO_PI = 0x1000
            
            # Open TUN device
            self.tun_fd = os.open('/dev/net/tun', os.O_RDWR)
            
            # Set TUN interface name
            ifr = struct.pack('16sH', self.interface_name.encode(), IFF_TUN | IFF_NO_PI)
            fcntl.ioctl(self.tun_fd, TUNSETIFF, ifr)
            
            # Configure IP address
            self._configure_interface_linux()
            
            return self.tun_fd
        except Exception as e:
            raise OSError(f"Failed to create TUN interface: {e}")
    
    def _create_tun_macos(self):
        """Create TUN interface on macOS"""
        try:
            # macOS uses utun devices
            for i in range(16):
                try:
                    dev = f'/dev/utun{i}'
                    self.tun_fd = os.open(dev, os.O_RDWR)
                    self.interface_name = f'utun{i}'
                    self._configure_interface_macos()
                    return self.tun_fd
                except OSError:
                    continue
            raise OSError("No available TUN device")
        except Exception as e:
            raise OSError(f"Failed to create TUN interface: {e}")
    
    def _create_tun_windows(self):
        """Create TUN interface on Windows"""
        # Windows requires TAP-Windows adapter
        # This is more complex and may require additional setup
        raise NotImplementedError("Windows TUN support requires TAP-Windows adapter")
    
    def _configure_interface_linux(self):
        """Configure TUN interface on Linux"""
        try:
            # Bring interface up
            subprocess.run(['ip', 'link', 'set', self.interface_name, 'up'], check=True, capture_output=True)
            
            # Set IP address
            subprocess.run(['ip', 'addr', 'add', f'{self.ip_address}/{self._netmask_to_cidr()}', 
                          'dev', self.interface_name], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to configure interface: {e}")
    
    def _configure_interface_macos(self):
        """Configure TUN interface on macOS"""
        try:
            # Set IP address using ifconfig
            subprocess.run(['ifconfig', self.interface_name, self.ip_address, 'netmask', self.netmask, 'up'],
                          check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to configure interface: {e}")
    
    def _netmask_to_cidr(self):
        """Convert netmask to CIDR notation"""
        parts = self.netmask.split('.')
        binary = ''.join([bin(int(x))[2:].zfill(8) for x in parts])
        return str(len(binary.rstrip('0')))
    
    def read_packet(self, max_size=2048):
        """Read packet from TUN interface"""
        if not self.tun_fd:
            raise OSError("TUN interface not created")
        
        try:
            # Linux/macOS: read directly from file descriptor
            if self.is_linux or self.is_macos:
                packet = os.read(self.tun_fd, max_size)
                return packet
            else:
                raise NotImplementedError("Platform not supported")
        except Exception as e:
            raise OSError(f"Failed to read from TUN: {e}")
    
    def write_packet(self, packet):
        """Write packet to TUN interface"""
        if not self.tun_fd:
            raise OSError("TUN interface not created")
        
        try:
            if self.is_linux or self.is_macos:
                os.write(self.tun_fd, packet)
            else:
                raise NotImplementedError("Platform not supported")
        except Exception as e:
            raise OSError(f"Failed to write to TUN: {e}")
    
    def close(self):
        """Close TUN interface"""
        if self.tun_fd:
            try:
                os.close(self.tun_fd)
                self.tun_fd = None
                
                # Bring interface down
                if self.is_linux:
                    subprocess.run(['ip', 'link', 'set', self.interface_name, 'down'], 
                                 capture_output=True)
                elif self.is_macos:
                    subprocess.run(['ifconfig', self.interface_name, 'down'],
                                 capture_output=True)
            except Exception as e:
                print(f"Warning: Error closing TUN interface: {e}")
    
    def setup_routing(self, server_ip, client_ip_range='10.9.0.0/24'):
        """Setup routing for VPN traffic"""
        try:
            if self.is_linux:
                # Add route for VPN network
                subprocess.run(['ip', 'route', 'add', client_ip_range, 'via', self.ip_address],
                             capture_output=True)
            elif self.is_macos:
                # macOS routing
                subprocess.run(['route', 'add', '-net', client_ip_range.split('/')[0], 
                              '-netmask', self.netmask, self.ip_address],
                             capture_output=True)
        except Exception as e:
            print(f"Warning: Failed to setup routing: {e}")

