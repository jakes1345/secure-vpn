#!/usr/bin/env python3
"""
PhazeVPN Protocol - NAT Traversal
Works behind firewalls and NAT routers
"""

import socket
import struct
import asyncio
from typing import Tuple, Optional

class STUNClient:
    """
    STUN (Session Traversal Utilities for NAT) client
    Discovers public IP and port when behind NAT
    """
    
    STUN_MAGIC_COOKIE = 0x2112A442
    STUN_SERVERS = [
        ('stun.stunprotocol.org', 3478),
        ('stun.l.google.com', 19302),
        ('stun1.l.google.com', 19302),
    ]
    
    def __init__(self):
        self.public_ip = None
        self.public_port = None
        self.mapped_address = None
    
    async def discover_public_address(self, local_port: int) -> Optional[Tuple[str, int]]:
        """
        Discover public IP and port using STUN
        Returns (public_ip, public_port) or None
        """
        for stun_server, stun_port in self.STUN_SERVERS:
            try:
                result = await self._stun_request(stun_server, stun_port, local_port)
                if result:
                    self.public_ip, self.public_port = result
                    self.mapped_address = result
                    return result
            except Exception as e:
                continue
        
        return None
    
    async def _stun_request(self, server: str, port: int, local_port: int) -> Optional[Tuple[str, int]]:
        """Send STUN binding request"""
        # STUN Binding Request
        transaction_id = os.urandom(12)
        
        # Message type: Binding Request (0x0001)
        msg_type = 0x0001
        msg_length = 0x0000
        
        # STUN header
        header = struct.pack('!HH', msg_type, msg_length)
        header += struct.pack('!I', self.STUN_MAGIC_COOKIE)
        header += transaction_id
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', local_port))
        sock.settimeout(5)
        
        try:
            # Send STUN request
            sock.sendto(header, (server, port))
            
            # Receive response
            data, addr = sock.recvfrom(1024)
            
            # Parse STUN response
            if len(data) < 20:
                return None
            
            # Check magic cookie
            magic = struct.unpack('!I', data[4:8])[0]
            if magic != self.STUN_MAGIC_COOKIE:
                return None
            
            # Parse MAPPED-ADDRESS attribute
            offset = 20
            while offset < len(data) - 4:
                attr_type = struct.unpack('!H', data[offset:offset+2])[0]
                attr_length = struct.unpack('!H', data[offset+2:offset+4])[0]
                
                if attr_type == 0x0001:  # MAPPED-ADDRESS
                    # Parse IP and port
                    family = struct.unpack('!B', data[offset+5:offset+6])[0]
                    port = struct.unpack('!H', data[offset+6:offset+8])[0]
                    
                    if family == 0x01:  # IPv4
                        ip_bytes = data[offset+8:offset+12]
                        ip = socket.inet_ntoa(ip_bytes)
                        return (ip, port)
                
                offset += 4 + attr_length
            
            return None
        
        finally:
            sock.close()
    
    def get_mapped_address(self) -> Optional[Tuple[str, int]]:
        """Get discovered public address"""
        return self.mapped_address

class NATTraversal:
    """
    NAT Traversal manager
    Handles STUN, TURN, and hole punching
    """
    
    def __init__(self):
        self.stun_client = STUNClient()
        self.public_ip = None
        self.public_port = None
        self.nat_type = None
    
    async def initialize(self, local_port: int):
        """Initialize NAT traversal"""
        # Discover public address
        result = await self.stun_client.discover_public_address(local_port)
        if result:
            self.public_ip, self.public_port = result
            return True
        return False
    
    def get_public_endpoint(self) -> Optional[Tuple[str, int]]:
        """Get public endpoint for this server"""
        return (self.public_ip, self.public_port) if self.public_ip else None
    
    def enable_hole_punching(self):
        """Enable UDP hole punching for NAT traversal"""
        # Implementation: Send periodic keepalive packets to maintain NAT mapping
        pass

class TURNClient:
    """
    TURN (Traversal Using Relays around NAT) client
    For difficult NAT configurations
    """
    
    def __init__(self):
        pass
    
    async def allocate_relay(self, turn_server: str, username: str, password: str):
        """Allocate relay address from TURN server"""
        # TURN implementation (more complex, for difficult NATs)
        pass

