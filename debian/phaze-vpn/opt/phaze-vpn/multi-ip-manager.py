#!/usr/bin/env python3
"""
PhazeVPN Multi-IP Manager
Manages multiple server IPs for load balancing and redundancy
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path('/opt/phaze-vpn') if Path('/opt/phaze-vpn').exists() else Path(__file__).parent.absolute()
SERVERS_DIR = BASE_DIR / 'servers'
CONFIG_FILE = BASE_DIR / 'servers.json'

class MultiIPManager:
    def __init__(self):
        self.servers_dir = SERVERS_DIR
        self.config_file = CONFIG_FILE
        self.servers_dir.mkdir(parents=True, exist_ok=True)
        self.load_config()
    
    def load_config(self):
        """Load server configuration"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                self.servers = json.load(f)
        else:
            self.servers = {}
            self.save_config()
    
    def save_config(self):
        """Save server configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.servers, f, indent=2)
    
    def add_server(self, name: str, ip: str, port: int = 1194, location: str = "Unknown", 
                   protocol: str = "openvpn", gaming: bool = False):
        """Add a new server"""
        server_config = {
            'name': name,
            'ip': ip,
            'port': port,
            'location': location,
            'protocol': protocol,  # 'openvpn' or 'wireguard'
            'gaming': gaming,
            'status': 'active',
            'load': 0,
            'latency': 0,
            'clients': 0
        }
        
        self.servers[name] = server_config
        self.save_config()
        
        # Create server directory and config
        server_dir = self.servers_dir / name
        server_dir.mkdir(exist_ok=True)
        
        # Copy appropriate config
        if protocol == 'wireguard':
            self._setup_wireguard_server(name, server_config)
        else:
            self._setup_openvpn_server(name, server_config)
        
        print(f"✅ Server '{name}' added")
        print(f"   IP: {ip}:{port}")
        print(f"   Location: {location}")
        print(f"   Protocol: {protocol}")
        print(f"   Gaming optimized: {gaming}")
    
    def _setup_openvpn_server(self, name: str, config: Dict):
        """Setup OpenVPN server"""
        server_dir = self.servers_dir / name
        
        # Choose config file
        if config.get('gaming'):
            base_config = BASE_DIR / 'config' / 'server-gaming.conf'
        else:
            base_config = BASE_DIR / 'config' / 'server.conf'
        
        if base_config.exists():
            import shutil
            shutil.copy(base_config, server_dir / 'server.conf')
            
            # Update port
            with open(server_dir / 'server.conf', 'r') as f:
                content = f.read()
            content = content.replace('port 1194', f'port {config["port"]}')
            with open(server_dir / 'server.conf', 'w') as f:
                f.write(content)
    
    def _setup_wireguard_server(self, name: str, config: Dict):
        """Setup WireGuard server"""
        # Run WireGuard setup script
        wg_script = BASE_DIR / 'scripts' / 'setup-wireguard.sh'
        if wg_script.exists():
            subprocess.run(['bash', str(wg_script), config['ip'], str(config['port'])])
    
    def list_servers(self):
        """List all servers"""
        if not self.servers:
            print("No servers configured")
            return
        
        print("\n" + "="*70)
        print("PhazeVPN Servers")
        print("="*70)
        print(f"{'Name':<15} {'IP':<20} {'Port':<8} {'Location':<15} {'Protocol':<12} {'Status':<10}")
        print("-"*70)
        
        for name, server in self.servers.items():
            status = server.get('status', 'unknown')
            protocol = server.get('protocol', 'openvpn')
            gaming = "🎮" if server.get('gaming') else ""
            
            print(f"{name:<15} {server['ip']:<20} {server['port']:<8} "
                  f"{server.get('location', 'Unknown'):<15} {protocol:<12} {status:<10} {gaming}")
        
        print("="*70 + "\n")
    
    def get_best_server(self, prefer_gaming: bool = False) -> Optional[Dict]:
        """Get best server based on latency and load"""
        import time
        
        best_server = None
        best_score = float('inf')
        
        for name, server in self.servers.items():
            if server.get('status') != 'active':
                continue
            
            # Prefer gaming servers if requested
            if prefer_gaming and not server.get('gaming'):
                continue
            
            # Ping server to get latency
            try:
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', server['ip']],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Parse latency
                    output = result.stdout.decode()
                    latency = 0
                    for line in output.split('\n'):
                        if 'time=' in line:
                            try:
                                latency = float(line.split('time=')[1].split()[0])
                                break
                            except:
                                pass
                    
                    # Get load (simplified - count active connections)
                    load = server.get('clients', 0)
                    
                    # Calculate score (lower is better)
                    # Latency: 70%, Load: 30%
                    score = (latency * 0.7) + (load * 0.3)
                    
                    if score < best_score:
                        best_score = score
                        best_server = server.copy()
                        best_server['latency'] = latency
                        best_server['score'] = score
            except:
                continue
        
        return best_server
    
    def generate_client_config(self, client_name: str, server_name: Optional[str] = None, 
                              prefer_gaming: bool = False, protocol: Optional[str] = None):
        """Generate client config for best server or specified server"""
        if server_name:
            server = self.servers.get(server_name)
            if not server:
                print(f"Error: Server '{server_name}' not found")
                return
        else:
            server = self.get_best_server(prefer_gaming=prefer_gaming)
            if not server:
                print("Error: No active servers available")
                return
        
        protocol = protocol or server.get('protocol', 'openvpn')
        
        if protocol == 'wireguard':
            self._generate_wireguard_config(client_name, server)
        else:
            self._generate_openvpn_config(client_name, server)
    
    def _generate_openvpn_config(self, client_name: str, server: Dict):
        """Generate OpenVPN client config"""
        # Use existing vpn-manager to generate config
        vpn_manager = BASE_DIR / 'vpn-manager.py'
        if vpn_manager.exists():
            # Temporarily set server IP
            os.environ['VPN_SERVER_IP'] = server['ip']
            os.environ['VPN_SERVER_PORT'] = str(server['port'])
            
            subprocess.run(['python3', str(vpn_manager), 'add-client', client_name])
    
    def _generate_wireguard_config(self, client_name: str, server: Dict):
        """Generate WireGuard client config"""
        wg_dir = BASE_DIR / 'wireguard'
        if wg_dir.exists():
            add_client_script = wg_dir / 'add-client.sh'
            if add_client_script.exists():
                subprocess.run(['bash', str(add_client_script), client_name])

def main():
    parser = argparse.ArgumentParser(description='PhazeVPN Multi-IP Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add server
    add_parser = subparsers.add_parser('add', help='Add a new server')
    add_parser.add_argument('name', help='Server name')
    add_parser.add_argument('ip', help='Server IP address')
    add_parser.add_argument('--port', type=int, default=1194, help='Server port (default: 1194)')
    add_parser.add_argument('--location', default='Unknown', help='Server location')
    add_parser.add_argument('--protocol', choices=['openvpn', 'wireguard'], default='openvpn')
    add_parser.add_argument('--gaming', action='store_true', help='Gaming optimized')
    
    # List servers
    subparsers.add_parser('list', help='List all servers')
    
    # Get best server
    best_parser = subparsers.add_parser('best', help='Get best server')
    best_parser.add_argument('--gaming', action='store_true', help='Prefer gaming servers')
    
    # Generate client config
    client_parser = subparsers.add_parser('client', help='Generate client config')
    client_parser.add_argument('client_name', help='Client name')
    client_parser.add_argument('--server', help='Specific server name')
    client_parser.add_argument('--gaming', action='store_true', help='Prefer gaming server')
    client_parser.add_argument('--protocol', choices=['openvpn', 'wireguard'], help='Protocol')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = MultiIPManager()
    
    if args.command == 'add':
        manager.add_server(
            args.name, args.ip, args.port, args.location,
            args.protocol, args.gaming
        )
    elif args.command == 'list':
        manager.list_servers()
    elif args.command == 'best':
        server = manager.get_best_server(prefer_gaming=args.gaming)
        if server:
            print(json.dumps(server, indent=2))
        else:
            print("No servers available")
    elif args.command == 'client':
        manager.generate_client_config(
            args.client_name, args.server, args.gaming, args.protocol
        )

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("Error: This script requires root privileges (use sudo)")
        sys.exit(1)
    main()

