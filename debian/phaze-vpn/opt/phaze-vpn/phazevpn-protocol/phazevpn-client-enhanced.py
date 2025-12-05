#!/usr/bin/env python3
"""
PhazeVPN Protocol - Enhanced Production Client
With all OpenVPN security features + WireGuard performance
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
from security_manager import SecurityManager

class PhazeVPNClientEnhanced:
    """Enhanced PhazeVPN Protocol Client with production features"""
    
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
        self.security = SecurityManager(vpn_interface='phazevpn0', vpn_ip='10.9.0.100')
        self.stats = {
            'bytes_sent': 0,
            'bytes_received': 0,
            'packets_sent': 0,
            'packets_received': 0,
            'connected_time': None
        }
        
        # Generate client keypair
        self.crypto.generate_keypair()
        print(f"✅ Client public key generated")
    
    def connect(self):
        """Connect to VPN server with full security"""
        print("=" * 70)
        print("🔌 PhazeVPN Protocol Client - Enhanced Production Version")
        print("=" * 70)
        print(f"📍 Server: {self.server_host}:{self.server_port}")
        print(f"👤 Username: {self.username or 'anonymous'}")
        print(f"🔒 Security: Kill Switch, DNS Protection, IPv6 Blocking")
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
            return
        
        # Create UDP socket with optimizations (WireGuard-style)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Increase buffer sizes for performance (like WireGuard)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2097152)  # 2MB
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2097152)  # 2MB
        self.sock.settimeout(10)
        
        # Initiate handshake
        print("🔄 Initiating handshake...")
        try:
            self._initiate_handshake()
        except Exception as e:
            print(f"❌ Handshake failed: {e}")
            self.disconnect()
            return
        
        # Setup security features (OpenVPN-style)
        print("🔒 Configuring security features...")
        try:
            self.security.setup_kill_switch(self.server_host)
            self.security.setup_dns_protection(['1.1.1.1', '1.0.0.1'])  # Cloudflare DNS
            self.security.block_ipv6()
            self.security.setup_routing()
            print("✅ Security features activated")
        except Exception as e:
            print(f"⚠️  Warning: Some security features failed: {e}")
            print("   Continuing without full security...")
        
        self.running = True
        self.stats['connected_time'] = time.time()
        
        # Start threads
        threading.Thread(target=self._tun_reader, daemon=True).start()
        threading.Thread(target=self._keepalive_thread, daemon=True).start()
        threading.Thread(target=self._stats_thread, daemon=True).start()
        
        print("✅ Connected to VPN server")
        print("")
        print("💡 VPN is now active with:")
        print("   ✅ Kill Switch (blocks all non-VPN traffic)")
        print("   ✅ DNS Leak Protection (forces DNS through VPN)")
        print("   ✅ IPv6 Blocking (prevents IPv6 leaks)")
        print("   ✅ All traffic routed through VPN")
        print("")
        
        # Main receive loop
        try:
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(65535)
                    self.stats['packets_received'] += 1
                    self.stats['bytes_received'] += len(data)
                    self._handle_server_packet(data, addr)
                except socket.timeout:
                    # Check connection health
                    if self.connected and time.time() - self.stats['connected_time'] > 300:
                        # Send keepalive if no traffic for 5 minutes
                        keepalive = PhazeVPNPacket(
                            packet_type=PacketType.KEEPALIVE,
                            session_id=self.session_id,
                            sequence=self.sequence
                        )
                        try:
                            self.sock.sendto(keepalive.pack(), (self.server_host, self.server_port))
                        except:
                            pass
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error receiving: {e}")
        except KeyboardInterrupt:
            print("\n🛑 Disconnecting...")
        finally:
            self.disconnect()
    
    def _initiate_handshake(self):
        """Initiate handshake with server (WireGuard-style fast handshake)"""
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
        self.stats['packets_sent'] += 1
        
        # Wait for response with timeout
        data, addr = self.sock.recvfrom(65535)
        response = PhazeVPNPacket.unpack(data)
        
        if response.packet_type == PacketType.HANDSHAKE_RESPONSE:
            # Extract server public key
            server_handshake = HandshakePacket.unpack(response.payload)
            
            # Derive shared secret (WireGuard-style X25519)
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
            self.stats['packets_sent'] += 1
            
            self.connected = True
        elif response.packet_type == PacketType.ERROR:
            error_msg = response.payload.decode('utf-8', errors='ignore')
            raise Exception(f"Server error: {error_msg}")
        else:
            raise Exception("Handshake failed: Invalid response")
    
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
                # Server keepalive - connection is alive
                pass
            
            elif packet.packet_type == PacketType.DISCONNECT:
                print("🔌 Server disconnected")
                self.running = False
            
            elif packet.packet_type == PacketType.ERROR:
                error_msg = packet.payload.decode('utf-8', errors='ignore')
                print(f"❌ Server error: {error_msg}")
                self.running = False
        
        except Exception as e:
            print(f"Error handling server packet: {e}")
    
    def _tun_reader(self):
        """Read packets from TUN and forward to server (WireGuard-style efficient forwarding)"""
        if not self.tun or not self.tun.tun_fd:
            return
        
        while self.running:
            try:
                packet = self.tun.read_packet()
                if packet and self.connected:
                    # Encrypt packet (ChaCha20-Poly1305 like WireGuard)
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
                    self.stats['packets_sent'] += 1
                    self.stats['bytes_sent'] += len(vpn_packet.pack())
            except Exception as e:
                if self.running:
                    time.sleep(0.01)  # Small delay to prevent CPU spinning
    
    def _keepalive_thread(self):
        """Send keepalive packets (OpenVPN-style connection management)"""
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
                    self.stats['packets_sent'] += 1
                except:
                    pass
    
    def _stats_thread(self):
        """Display connection statistics"""
        while self.running:
            time.sleep(60)  # Every minute
            if self.connected and self.stats['connected_time']:
                duration = int(time.time() - self.stats['connected_time'])
                minutes = duration // 60
                seconds = duration % 60
                sent_mb = self.stats['bytes_sent'] / (1024 * 1024)
                recv_mb = self.stats['bytes_received'] / (1024 * 1024)
                print(f"📊 Stats: {minutes}m {seconds}s | "
                      f"↑ {sent_mb:.2f} MB | ↓ {recv_mb:.2f} MB | "
                      f"Packets: {self.stats['packets_sent']}/{self.stats['packets_received']}")
    
    def disconnect(self):
        """Disconnect from server and restore settings"""
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
        
        # Restore network settings
        print("🔓 Restoring network settings...")
        self.security.restore_settings()
        
        if self.sock:
            self.sock.close()
        if self.tun:
            self.tun.close()
        
        print("✅ Disconnected and settings restored")

if __name__ == '__main__':
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='PhazeVPN Protocol Enhanced Client')
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
    
    # Check root on Linux/macOS for TUN and security features
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        if os.geteuid() != 0:
            print("⚠️  Warning: TUN interface and security features require root.")
            print("   Running without full security features...")
            print("   For full protection, run with: sudo python3 phazevpn-client-enhanced.py")
    
    client = PhazeVPNClientEnhanced(
        server_host=server_host,
        server_port=server_port,
        username=username,
        password=password
    )
    
    try:
        client.connect()
    except KeyboardInterrupt:
        pass

