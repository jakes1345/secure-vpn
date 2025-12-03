#!/usr/bin/env python3
"""
PhazeVPN Protocol - Packet Format and Protocol Implementation
Custom protocol specification for PhazeVPN
"""

import struct
from enum import IntEnum

# Protocol constants
MAGIC_NUMBER = b'PHAZ'
PROTOCOL_VERSION = 1

class PacketType(IntEnum):
    """Packet types in PhazeVPN Protocol"""
    HANDSHAKE_INIT = 0x01      # Client initiates handshake
    HANDSHAKE_RESPONSE = 0x02   # Server responds to handshake
    HANDSHAKE_COMPLETE = 0x03  # Client completes handshake
    DATA = 0x10                 # Encrypted data packet
    KEEPALIVE = 0x20            # Keepalive packet
    DISCONNECT = 0x30           # Disconnect notification
    ERROR = 0x40                # Error message
    AUTH_REQUEST = 0x50         # Authentication request
    AUTH_RESPONSE = 0x51        # Authentication response

class PhazeVPNPacket:
    """PhazeVPN Protocol packet structure"""
    
    HEADER_SIZE = 16
    MAX_PAYLOAD_SIZE = 16384  # 16KB max payload
    
    def __init__(self, packet_type=PacketType.DATA, payload=b'', session_id=0, sequence=0):
        self.magic = MAGIC_NUMBER
        self.version = PROTOCOL_VERSION
        self.packet_type = packet_type
        self.sequence = sequence
        self.session_id = session_id
        self.payload = payload
        self.length = len(payload)
    
    def pack(self):
        """Pack packet into bytes"""
        if len(self.payload) > self.MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload too large: {len(self.payload)} bytes")
        
        header = struct.pack(
            '!4s B B I I H',  # Magic, Version, Type, Sequence, SessionID, Length
            self.magic,
            self.version,
            self.packet_type,
            self.sequence,
            self.session_id,
            self.length
        )
        
        return header + self.payload
    
    @classmethod
    def unpack(cls, data):
        """Unpack bytes into packet"""
        if len(data) < cls.HEADER_SIZE:
            raise ValueError(f"Packet too short: {len(data)} bytes")
        
        header = data[:cls.HEADER_SIZE]
        magic, version, packet_type, sequence, session_id, length = struct.unpack(
            '!4s B B I I H', header
        )
        
        if magic != MAGIC_NUMBER:
            raise ValueError(f"Invalid magic number: {magic}")
        
        if version != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")
        
        if length > cls.MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload length too large: {length}")
        
        payload = data[cls.HEADER_SIZE:cls.HEADER_SIZE + length]
        
        if len(payload) < length:
            raise ValueError(f"Incomplete payload: got {len(payload)}, expected {length}")
        
        packet = cls(
            packet_type=PacketType(packet_type),
            payload=payload,
            session_id=session_id,
            sequence=sequence
        )
        
        return packet
    
    def __repr__(self):
        return (f"PhazeVPNPacket(type={self.packet_type.name}, "
                f"seq={self.sequence}, session={self.session_id}, "
                f"len={self.length})")

class HandshakePacket:
    """Handshake packet with public key and VPN mode"""
    
    def __init__(self, public_key_bytes, username=None, password_hash=None, vpn_mode='normal'):
        self.public_key = public_key_bytes
        self.username = username
        self.password_hash = password_hash
        self.vpn_mode = vpn_mode  # normal, semi_ghost, full_ghost, tor_ghost
    
    def pack(self):
        """Pack handshake data"""
        data = struct.pack('!H', len(self.public_key)) + self.public_key
        
        if self.username:
            username_bytes = self.username.encode('utf-8')
            data += struct.pack('!H', len(username_bytes)) + username_bytes
        else:
            data += struct.pack('!H', 0)
        
        if self.password_hash:
            data += struct.pack('!H', len(self.password_hash)) + self.password_hash
        else:
            data += struct.pack('!H', 0)
        
        # Add VPN mode
        mode_bytes = self.vpn_mode.encode('utf-8')
        data += struct.pack('!H', len(mode_bytes)) + mode_bytes
        
        return data
    
    @classmethod
    def unpack(cls, data):
        """Unpack handshake data"""
        offset = 0
        
        # Public key
        key_len = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        public_key = data[offset:offset+key_len]
        offset += key_len
        
        # Username
        username_len = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        username = None
        if username_len > 0:
            username = data[offset:offset+username_len].decode('utf-8')
            offset += username_len
        
        # Password hash
        password_len = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        password_hash = None
        if password_len > 0:
            password_hash = data[offset:offset+password_len]
            offset += password_len
        
        # VPN mode (new in v2)
        vpn_mode = 'normal'  # Default
        if offset < len(data):
            try:
                mode_len = struct.unpack('!H', data[offset:offset+2])[0]
                offset += 2
                if mode_len > 0 and offset + mode_len <= len(data):
                    vpn_mode = data[offset:offset+mode_len].decode('utf-8')
            except:
                pass  # Backward compatible
        
        return cls(public_key, username, password_hash, vpn_mode)

