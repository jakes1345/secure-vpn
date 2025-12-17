#!/usr/bin/env python3
"""
PhazeVPN Protocol - Custom VPN Client
Completely independent VPN client implementation
"""

import socket
import threading
import time
import sys
import os
from pathlib import Path

from protocol import PhazeVPNPacket, PacketType, HandshakePacket
from crypto import PhazeVPNCrypto
from tun_manager import TUNManager

class PhazeVPNClient:
    """Custom PhazeVPN Protocol Client"""
    
    def __init__(self, server_host, server_port=51821, username=None, password=None):
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.password = password
        self.running = False
        self.sock = None
        self.session_id = 0
        self.crypto = PhazeVPNCrypto()
        self.tun = None
        self.connected = False
        self.sequence = 0
        
        # Generate client keypair
        self.crypto.generate_keypair()
        print(f"✅ Client public key generated")
    
    def connect(self):
        """Connect to VPN server"""
        print("=" * 70)
        print("🔌 PhazeVPN Protocol Client - Connecting")
        print("=" * 70)
        print(f"📍 Server: {self.server_host}:{self.server_port}")
        print(f"👤 Username: {self.username or 'anonymous'}")
        print("=" * 70)
        print("")
        
        # Create TUN interface
        try:
            self.tun = TUNManager(interface_name='phazevpn0', ip_address='10.9.0.100')
            self.tun.create_tun()
            print(f"✅ TUN interface created: phazevpn0")
        except Exception as e:
            print(f"⚠️  Warning: Could not create TUN interface: {e}")
            print("   Client will run in relay mode only")
            if sys.platform != 'win32':
                print("   Try running with sudo for TUN access")
        
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10)
        
        # Initiate handshake
        print("🔄 Initiating handshake...")
        self._initiate_handshake()
        
        self.running = True
        
        # Start threads
        threading.Thread(target=self._tun_reader, daemon=True).start()
        threading.Thread(target=self._keepalive_thread, daemon=True).start()
        
        print("✅ Connected to VPN server")
        print("")
        
        # Main receive loop
        try:
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(65535)
                    self._handle_server_packet(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error receiving: {e}")
        except KeyboardInterrupt:
            print("\n🛑 Disconnecting...")
        finally:
            self.disconnect()
    
    def _initiate_handshake(self):
        """Initiate handshake with server"""
        # Prepare handshake data
        public_key = self.crypto.get_public_key_bytes()
        
        # Hash password if provided
        password_hash = None
        if self.password:
            password_hash, salt = self.crypto.hash_password(self.password)
        
        handshake = HandshakePacket(
            public_key_bytes=public_key,
            username=self.username,
            password_hash=password_hash
        )
        
        # Send handshake init
        packet = PhazeVPNPacket(
            packet_type=PacketType.HANDSHAKE_INIT,
            payload=handshake.pack(),
            session_id=0,
            sequence=0
        )
        
        self.sock.sendto(packet.pack(), (self.server_host, self.server_port))
        
        # Wait for response
        data, addr = self.sock.recvfrom(65535)
        response = PhazeVPNPacket.unpack(data)
        
        if response.packet_type == PacketType.HANDSHAKE_RESPONSE:
            # Extract server public key
            server_handshake = HandshakePacket.unpack(response.payload)
            
            # Derive shared secret
            self.crypto.derive_shared_secret(server_handshake.public_key)
            session_key, salt = self.crypto.derive_session_key()
            
            self.session_id = response.session_id
            print(f"✅ Handshake complete - Session ID: {self.session_id}")
            
            # Send handshake complete
            complete_packet = PhazeVPNPacket(
                packet_type=PacketType.HANDSHAKE_COMPLETE,
                session_id=self.session_id,
                sequence=0
            )
            self.sock.sendto(complete_packet.pack(), (self.server_host, self.server_port))
            
            self.connected = True
        else:
            raise Exception("Handshake failed")
    
    def _handle_server_packet(self, data, addr):
        """Handle packet from server"""
        try:
            packet = PhazeVPNPacket.unpack(data)
            
            if packet.packet_type == PacketType.DATA:
                # Decrypt and forward to TUN
                decrypted = self.crypto.decrypt_packet(packet.payload)
                if self.tun and self.tun.tun_fd:
                    self.tun.write_packet(decrypted)
            
            elif packet.packet_type == PacketType.KEEPALIVE:
                # Respond to keepalive
                pass
            
            elif packet.packet_type == PacketType.DISCONNECT:
                print("🔌 Server disconnected")
                self.running = False
            
            elif packet.packet_type == PacketType.ERROR:
                error_msg = packet.payload.decode('utf-8', errors='ignore')
                print(f"❌ Server error: {error_msg}")
        
        except Exception as e:
            print(f"Error handling server packet: {e}")
    
    def _tun_reader(self):
        """Read packets from TUN and forward to server"""
        if not self.tun or not self.tun.tun_fd:
            return
        
        while self.running:
            try:
                packet = self.tun.read_packet()
                if packet and self.connected:
                    # Encrypt packet
                    encrypted = self.crypto.encrypt_packet(packet)
                    
                    # Create VPN packet
                    vpn_packet = PhazeVPNPacket(
                        packet_type=PacketType.DATA,
                        payload=encrypted,
                        session_id=self.session_id,
                        sequence=self.sequence
                    )
                    self.sequence += 1
                    
                    # Send to server
                    self.sock.sendto(vpn_packet.pack(), (self.server_host, self.server_port))
            except Exception as e:
                if self.running:
                    time.sleep(0.1)
    
    def _keepalive_thread(self):
        """Send keepalive packets"""
        while self.running:
            time.sleep(30)  # Every 30 seconds
            if self.connected:
                keepalive = PhazeVPNPacket(
                    packet_type=PacketType.KEEPALIVE,
                    session_id=self.session_id,
                    sequence=self.sequence
                )
                try:
                    self.sock.sendto(keepalive.pack(), (self.server_host, self.server_port))
                except:
                    pass
    
    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            disconnect_packet = PhazeVPNPacket(
                packet_type=PacketType.DISCONNECT,
                session_id=self.session_id
            )
            try:
                self.sock.sendto(disconnect_packet.pack(), (self.server_host, self.server_port))
            except:
                pass
        
        self.running = False
        self.connected = False
        
        if self.sock:
            self.sock.close()
        if self.tun:
            self.tun.close()
        
        print("✅ Disconnected")

if __name__ == '__main__':
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='PhazeVPN Protocol Client')
    parser.add_argument('--server', help='Server hostname or IP')
    parser.add_argument('--port', type=int, default=51821, help='Server port')
    parser.add_argument('--username', help='Username')
    parser.add_argument('--password', help='Password')
    parser.add_argument('--config', help='Path to .phazevpn config file')
    
    args = parser.parse_args()
    
    # Load config from file if provided
    server_host = args.server
    server_port = args.port
    username = args.username
    password = args.password
    
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            sys.exit(1)
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Try JSON format first (from generate_phazevpn_config.py)
            try:
                config = json.loads(content)
                # Override with config file values if not provided via command line
                if not server_host:
                    server_host = config.get('server', {}).get('host')
                if not server_port:
                    server_port = config.get('server', {}).get('port', 51821)
                if not username:
                    username = config.get('authentication', {}).get('username')
                if not password:
                    password = config.get('authentication', {}).get('password')
            except json.JSONDecodeError:
                # Try INI format (from ClientManager)
                import configparser
                config_parser = configparser.ConfigParser()
                config_parser.read_string(content)
                if config_parser.has_section('Connection'):
                    if not server_host:
                        server_host = config_parser.get('Connection', 'server', fallback=None)
                    if not server_port:
                        server_port = config_parser.getint('Connection', 'port', fallback=51821)
                    if not username:
                        username = config_parser.get('Connection', 'username', fallback=None)
                    if not password:
                        password = config_parser.get('Connection', 'password', fallback=None)
            
            print(f"✅ Loaded config from: {config_path}")
        except Exception as e:
            print(f"❌ Error loading config file: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    if not server_host:
        print("❌ Server host required. Use --server or --config")
        parser.print_help()
        sys.exit(1)
    
    # Check root on Linux/macOS for TUN
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        if os.geteuid() != 0:
            print("⚠️  Warning: TUN interface requires root. Running without TUN...")
    
    client = PhazeVPNClient(
        server_host=server_host,
        server_port=server_port,
        username=username,
        password=password
    )
    
    try:
        client.connect()
    except KeyboardInterrupt:
        pass

