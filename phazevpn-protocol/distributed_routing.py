#!/usr/bin/env python3
"""
Distributed VPN Routing - Route Through User IPs
Makes correlation EXTREMELY difficult by using user IPs as exit nodes
"""

import os
import random
import time
import asyncio
from typing import List, Dict, Optional, Tuple
from collections import deque
import hashlib

class UserIPPool:
    """
    Pool of user IPs that can be used as exit nodes
    Each user's IP becomes a potential exit point
    """
    
    def __init__(self):
        self.user_ips = {}  # user_id -> (ip, port, last_seen, trust_score)
        self.available_ips = deque()  # Queue of available IPs
        self.trust_threshold = 0.7  # Minimum trust score to use as exit
        
    def add_user_ip(self, user_id: str, ip: str, port: int, trust_score: float = 1.0):
        """Add user IP to pool"""
        self.user_ips[user_id] = {
            'ip': ip,
            'port': port,
            'last_seen': time.time(),
            'trust_score': trust_score,
            'usage_count': 0,
            'active': True
        }
        
        if trust_score >= self.trust_threshold:
            self.available_ips.append(user_id)
    
    def get_random_exit_ip(self) -> Optional[Tuple[str, int]]:
        """Get random user IP to use as exit node"""
        if not self.available_ips:
            return None
        
        # Get random user from available pool
        user_id = random.choice(list(self.available_ips))
        
        if user_id in self.user_ips:
            user_data = self.user_ips[user_id]
            user_data['usage_count'] += 1
            user_data['last_seen'] = time.time()
            return (user_data['ip'], user_data['port'])
        
        return None
    
    def get_chain_of_ips(self, chain_length: int = 3) -> List[Tuple[str, int]]:
        """
        Get chain of user IPs for multi-hop routing
        Your traffic → User IP 1 → User IP 2 → User IP 3 → Destination
        """
        chain = []
        used_users = set()
        
        for _ in range(chain_length):
            # Get random user IP (not already in chain)
            available = [uid for uid in self.available_ips if uid not in used_users]
            if not available:
                break
            
            user_id = random.choice(available)
            used_users.add(user_id)
            
            if user_id in self.user_ips:
                user_data = self.user_ips[user_id]
                chain.append((user_data['ip'], user_data['port']))
        
        return chain
    
    def update_trust_score(self, user_id: str, success: bool):
        """Update trust score based on routing success"""
        if user_id in self.user_ips:
            if success:
                self.user_ips[user_id]['trust_score'] = min(1.0, 
                    self.user_ips[user_id]['trust_score'] + 0.01)
            else:
                self.user_ips[user_id]['trust_score'] = max(0.0,
                    self.user_ips[user_id]['trust_score'] - 0.05)
            
            # Remove from pool if trust too low
            if self.user_ips[user_id]['trust_score'] < self.trust_threshold:
                if user_id in self.available_ips:
                    self.available_ips.remove(user_id)


class DistributedRouter:
    """
    Routes traffic through distributed user IPs
    Makes correlation EXTREMELY difficult
    """
    
    def __init__(self):
        self.ip_pool = UserIPPool()
        self.routing_mode = 'random'  # random, chain, round_robin
        self.chain_length = 3  # Number of user IPs in chain
        
    def add_user(self, user_id: str, ip: str, port: int):
        """Add user to routing pool"""
        self.ip_pool.add_user_ip(user_id, ip, port)
    
    def route_through_users(self, packet: bytes, destination: Tuple[str, int]) -> List[Tuple[bytes, Tuple[str, int]]]:
        """
        Route packet through chain of user IPs
        Returns list of (encrypted_packet, next_hop) tuples
        """
        # Get chain of user IPs
        chain = self.ip_pool.get_chain_of_ips(self.chain_length)
        
        if not chain:
            # No users available, route directly
            return [(packet, destination)]
        
        # Encrypt packet for each hop (onion routing style)
        routed_packets = []
        current_packet = packet
        
        # Encrypt from last hop to first (onion routing)
        for i, (user_ip, user_port) in enumerate(reversed(chain)):
            # Encrypt packet for this hop
            encrypted = self._encrypt_for_hop(current_packet, user_ip, i)
            
            # Add routing header (encrypted destination)
            if i == len(chain) - 1:
                # Last hop - route to final destination
                next_hop = destination
            else:
                # Intermediate hop - route to next user in chain
                next_hop = chain[len(chain) - i - 2]
            
            routed_packets.insert(0, (encrypted, next_hop))
            current_packet = encrypted
        
        return routed_packets
    
    def _encrypt_for_hop(self, packet: bytes, hop_ip: str, hop_index: int) -> bytes:
        """Encrypt packet for specific hop (onion routing)"""
        # Generate hop-specific key
        key = hashlib.sha256(f"{hop_ip}:{hop_index}:{time.time()}".encode()).digest()[:32]
        
        # Simple XOR encryption (in production, use proper encryption)
        encrypted = bytes(a ^ b for a, b in zip(packet, key * (len(packet) // len(key) + 1)))
        
        return encrypted
    
    def get_exit_ip(self) -> Optional[Tuple[str, int]]:
        """Get random user IP to use as exit node"""
        return self.ip_pool.get_random_exit_ip()


class SecureUserRouting:
    """
    Secure routing through user IPs
    Users can't see other users' traffic (encrypted)
    """
    
    def __init__(self):
        self.router = DistributedRouter()
        self.user_sessions = {}  # user_id -> session_info
        self.routing_enabled = True
        
    def register_user(self, user_id: str, ip: str, port: int):
        """Register user for distributed routing"""
        self.router.add_user(user_id, ip, port)
        self.user_sessions[user_id] = {
            'ip': ip,
            'port': port,
            'registered_at': time.time(),
            'routing_enabled': True
        }
    
    def route_packet(self, packet: bytes, destination: Tuple[str, int], 
                    use_user_routing: bool = True) -> List[Tuple[bytes, Tuple[str, int]]]:
        """
        Route packet through user IPs if enabled
        """
        if not use_user_routing or not self.routing_enabled:
            return [(packet, destination)]
        
        # Route through user IP chain
        return self.router.route_through_users(packet, destination)
    
    def get_user_exit_ip(self) -> Optional[Tuple[str, int]]:
        """Get random user IP to use as exit"""
        return self.router.get_exit_ip()
    
    def enable_routing_for_user(self, user_id: str):
        """Enable routing for specific user"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]['routing_enabled'] = True
    
    def disable_routing_for_user(self, user_id: str):
        """Disable routing for specific user"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]['routing_enabled'] = False


class DistributedVPNSession:
    """
    VPN session that routes through distributed user IPs
    Makes correlation EXTREMELY difficult
    """
    
    def __init__(self, session_id: str, user_routing: SecureUserRouting):
        self.session_id = session_id
        self.user_routing = user_routing
        self.routing_chain = []
        self.current_exit_ip = None
        
    async def establish_routing_chain(self):
        """Establish routing chain through user IPs"""
        # Get chain of user IPs
        exit_ip = self.user_routing.get_user_exit_ip()
        if exit_ip:
            self.current_exit_ip = exit_ip
            self.routing_chain = [exit_ip]
            return True
        return False
    
    async def route_packet(self, packet: bytes, destination: Tuple[str, int]) -> List[Tuple[bytes, Tuple[str, int]]]:
        """Route packet through user IP chain"""
        return self.user_routing.route_packet(packet, destination, use_user_routing=True)
    
    def get_exit_ip(self) -> Optional[Tuple[str, int]]:
        """Get current exit IP"""
        return self.current_exit_ip


class DistributedVPNServer:
    """
    VPN server with distributed routing through user IPs
    """
    
    def __init__(self):
        self.user_routing = SecureUserRouting()
        self.active_sessions = {}  # session_id -> DistributedVPNSession
        self.routing_enabled = True
        
    def register_user_for_routing(self, user_id: str, ip: str, port: int):
        """Register user to participate in distributed routing"""
        self.user_routing.register_user(user_id, ip, port)
        print(f"✅ User {user_id} registered for distributed routing ({ip}:{port})")
    
    async def create_distributed_session(self, session_id: str) -> DistributedVPNSession:
        """Create VPN session with distributed routing"""
        session = DistributedVPNSession(session_id, self.user_routing)
        await session.establish_routing_chain()
        self.active_sessions[session_id] = session
        return session
    
    async def route_through_users(self, session_id: str, packet: bytes, 
                                 destination: Tuple[str, int]) -> List[Tuple[bytes, Tuple[str, int]]]:
        """Route packet through user IP chain"""
        if session_id not in self.active_sessions:
            return [(packet, destination)]
        
        session = self.active_sessions[session_id]
        return await session.route_packet(packet, destination)
    
    def get_user_count(self) -> int:
        """Get number of users in routing pool"""
        return len(self.user_routing.user_sessions)
    
    def get_available_exit_ips(self) -> List[Tuple[str, int]]:
        """Get list of available exit IPs"""
        ips = []
        for user_id, session in self.user_routing.user_sessions.items():
            if session.get('routing_enabled', False):
                ips.append((session['ip'], session['port']))
        return ips

