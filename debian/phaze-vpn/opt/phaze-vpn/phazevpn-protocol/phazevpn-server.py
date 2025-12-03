#!/usr/bin/env python3
"""
PhazeVPN Protocol - Custom VPN Server
Completely independent VPN server implementation
"""

import socket
import threading
import time
import json
import os
from pathlib import Path
from collections import defaultdict
import select

from protocol import PhazeVPNPacket, PacketType, HandshakePacket, PROTOCOL_VERSION
from crypto import PhazeVPNCrypto
from tun_manager import TUNManager

class PhazeVPNServer:
    """Custom PhazeVPN Protocol Server"""
    
    def __init__(self, host='0.0.0.0', port=51820, vpn_network='10.9.0.0/24'):
        self.host = host
        self.port = port
        self.vpn_network = vpn_network
        self.server_ip = '10.9.0.1'
        self.running = False
        self.sock = None
        self.clients = {}  # session_id -> client info
        self.client_ips = {}  # session_id -> assigned IP
        self.next_client_ip = 2  # Start from 10.9.0.2
        self.crypto = PhazeVPNCrypto()
        self.tun = None
        self.users_db = Path('/opt/secure-vpn/phazevpn-users.json')
        
        # Load users database
        self.users = self._load_users()
        
        # Generate server keypair
        self.crypto.generate_keypair()
        print(f"✅ Server public key generated")
    
    def _load_users(self):
        """Load users database"""
        if self.users_db.exists():
            try:
                with open(self.users_db, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_users(self):
        """Save users database"""
        self.users_db.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_db, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def start(self):
        """Start VPN server"""
        print("=" * 70)
        print("🚀 PhazeVPN Protocol Server - Starting")
        print("=" * 70)
        print(f"📍 Listening on {self.host}:{self.port}")
        print(f"🌐 VPN Network: {self.vpn_network}")
        print(f"🔐 Protocol: PhazeVPN v{PROTOCOL_VERSION}")
        print("=" * 70)
        print("")
        
        # Create TUN interface
        try:
            self.tun = TUNManager(interface_name='phazevpn0', ip_address=self.server_ip)
            self.tun.create_tun()
            print(f"✅ TUN interface created: phazevpn0 ({self.server_ip})")
        except Exception as e:
            print(f"⚠️  Warning: Could not create TUN interface: {e}")
            print("   Server will run in relay mode only")
        
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.setblocking(False)
        
        self.running = True
        
        # Start threads
        threading.Thread(target=self._tun_reader, daemon=True).start()
        threading.Thread(target=self._keepalive_thread, daemon=True).start()
        
        print("✅ Server started and ready for connections")
        print("")
        
        # Main receive loop
        try:
            while self.running:
                ready, _, _ = select.select([self.sock], [], [], 1.0)
                if ready:
                    try:
                        data, addr = self.sock.recvfrom(65535)
                        threading.Thread(target=self._handle_client, args=(data, addr), daemon=True).start()
                    except Exception as e:
                        print(f"Error receiving: {e}")
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
        finally:
            self.stop()
    
    def _handle_client(self, data, addr):
        """Handle incoming client packet"""
        try:
            packet = PhazeVPNPacket.unpack(data)
            
            if packet.packet_type == PacketType.HANDSHAKE_INIT:
                self._handle_handshake_init(packet, addr)
            elif packet.packet_type == PacketType.HANDSHAKE_COMPLETE:
                self._handle_handshake_complete(packet, addr)
            elif packet.packet_type == PacketType.DATA:
                self._handle_data_packet(packet, addr)
            elif packet.packet_type == PacketType.KEEPALIVE:
                self._handle_keepalive(packet, addr)
            elif packet.packet_type == PacketType.DISCONNECT:
                self._handle_disconnect(packet, addr)
            else:
                print(f"Unknown packet type: {packet.packet_type}")
        
        except Exception as e:
            print(f"Error handling packet from {addr}: {e}")
    
    def _handle_handshake_init(self, packet, addr):
        """Handle initial handshake from client"""
        try:
            handshake = HandshakePacket.unpack(packet.payload)
            
            # Authenticate user
            authenticated = False
            username = handshake.username
            
            if username and username in self.users:
                stored_hash = bytes.fromhex(self.users[username]['password_hash'])
                stored_salt = bytes.fromhex(self.users[username]['password_salt'])
                if handshake.password_hash:
                    authenticated = self.crypto.verify_password(
                        '',  # Password already hashed by client
                        stored_hash,
                        stored_salt
                    )
            
            if not authenticated:
                # For now, allow any connection (can add proper auth later)
                authenticated = True
                username = username or f"user_{len(self.clients)}"
            
            # Generate session
            session_id = int(time.time() * 1000) % 0xFFFFFFFF
            client_ip = f"10.9.0.{self.next_client_ip}"
            self.next_client_ip += 1
            
            # Derive shared secret
            self.crypto.derive_shared_secret(handshake.public_key)
            session_key, salt = self.crypto.derive_session_key()
            
            # Store client info
            self.clients[session_id] = {
                'addr': addr,
                'username': username,
                'session_key': session_key.hex(),
                'salt': salt.hex(),
                'client_ip': client_ip,
                'last_seen': time.time(),
                'public_key': handshake.public_key.hex()
            }
            self.client_ips[session_id] = client_ip
            
            # Send handshake response
            server_public_key = self.crypto.get_public_key_bytes()
            response_handshake = HandshakePacket(server_public_key)
            
            response_packet = PhazeVPNPacket(
                packet_type=PacketType.HANDSHAKE_RESPONSE,
                payload=response_handshake.pack(),
                session_id=session_id,
                sequence=0
            )
            
            self.sock.sendto(response_packet.pack(), addr)
            print(f"✅ Handshake initiated with {username} ({addr[0]}) - Session: {session_id}")
        
        except Exception as e:
            print(f"Error in handshake init: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_handshake_complete(self, packet, addr):
        """Handle handshake completion"""
        session_id = packet.session_id
        if session_id in self.clients:
            client = self.clients[session_id]
            client['last_seen'] = time.time()
            client['connected'] = True
            print(f"✅ Client {client['username']} connected - IP: {client['client_ip']}")
    
    def _handle_data_packet(self, packet, addr):
        """Handle encrypted data packet"""
        session_id = packet.session_id
        if session_id not in self.clients:
            return
        
        client = self.clients[session_id]
        client['last_seen'] = time.time()
        
        # Decrypt packet
        try:
            # Restore crypto state for this client
            self.crypto.session_key = bytes.fromhex(client['session_key'])
            decrypted = self.crypto.decrypt_packet(packet.payload)
            
            # Forward to TUN interface
            if self.tun and self.tun.tun_fd:
                self.tun.write_packet(decrypted)
        
        except Exception as e:
            print(f"Error decrypting/forwarding packet: {e}")
    
    def _handle_keepalive(self, packet, addr):
        """Handle keepalive packet"""
        session_id = packet.session_id
        if session_id in self.clients:
            self.clients[session_id]['last_seen'] = time.time()
    
    def _handle_disconnect(self, packet, addr):
        """Handle disconnect"""
        session_id = packet.session_id
        if session_id in self.clients:
            client = self.clients[session_id]
            print(f"🔌 Client {client['username']} disconnected")
            del self.clients[session_id]
            if session_id in self.client_ips:
                del self.client_ips[session_id]
    
    def _tun_reader(self):
        """Read packets from TUN and forward to clients"""
        if not self.tun or not self.tun.tun_fd:
            return
        
        while self.running:
            try:
                packet = self.tun.read_packet()
                if packet:
                    # Forward to all connected clients
                    for session_id, client in list(self.clients.items()):
                        if client.get('connected'):
                            try:
                                # Encrypt for this client
                                self.crypto.session_key = bytes.fromhex(client['session_key'])
                                encrypted = self.crypto.encrypt_packet(packet)
                                
                                # Create packet
                                vpn_packet = PhazeVPNPacket(
                                    packet_type=PacketType.DATA,
                                    payload=encrypted,
                                    session_id=session_id,
                                    sequence=0
                                )
                                
                                self.sock.sendto(vpn_packet.pack(), client['addr'])
                            except Exception as e:
                                print(f"Error forwarding to client: {e}")
            except Exception as e:
                if self.running:
                    time.sleep(0.1)
    
    def _keepalive_thread(self):
        """Send keepalive and cleanup stale connections"""
        while self.running:
            time.sleep(30)  # Every 30 seconds
            
            current_time = time.time()
            stale_sessions = []
            
            for session_id, client in self.clients.items():
                if current_time - client['last_seen'] > 120:  # 2 minutes timeout
                    stale_sessions.append(session_id)
                else:
                    # Send keepalive
                    keepalive = PhazeVPNPacket(
                        packet_type=PacketType.KEEPALIVE,
                        session_id=session_id
                    )
                    try:
                        self.sock.sendto(keepalive.pack(), client['addr'])
                    except:
                        pass
            
            # Remove stale sessions
            for session_id in stale_sessions:
                print(f"🔌 Removing stale session: {session_id}")
                del self.clients[session_id]
                if session_id in self.client_ips:
                    del self.client_ips[session_id]
    
    def stop(self):
        """Stop server"""
        self.running = False
        if self.sock:
            self.sock.close()
        if self.tun:
            self.tun.close()
        print("✅ Server stopped")

if __name__ == '__main__':
    import sys
    
    # Check root
    if os.geteuid() != 0:
        print("❌ Error: Server must run as root (for TUN interface)")
        sys.exit(1)
    
    server = PhazeVPNServer(host='0.0.0.0', port=51820)
    server.start()

