#!/bin/bash
# PhazeVPN - Multi-IP Setup Script
# Allows using multiple server IPs for load balancing and redundancy

set -e

VPN_DIR="${VPN_DIR:-/opt/phaze-vpn}"
CONFIG_DIR="$VPN_DIR/config"
SERVERS_DIR="$VPN_DIR/servers"
SCRIPTS_DIR="$VPN_DIR/scripts"

echo "=========================================="
echo "PhazeVPN Multi-IP Setup"
echo "=========================================="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Create directories
mkdir -p "$SERVERS_DIR"
mkdir -p "$CONFIG_DIR/multi-ip"

# Function to add a new server IP
add_server_ip() {
    local server_name=$1
    local server_ip=$2
    local server_port=${3:-1194}
    local server_location=${4:-"Unknown"}
    
    echo "Adding server: $server_name"
    echo "  IP: $server_ip"
    echo "  Port: $server_port"
    echo "  Location: $server_location"
    
    # Create server config directory
    mkdir -p "$SERVERS_DIR/$server_name"
    
    # Copy base config
    if [ -f "$CONFIG_DIR/server-gaming.conf" ]; then
        cp "$CONFIG_DIR/server-gaming.conf" "$SERVERS_DIR/$server_name/server.conf"
    else
        cp "$CONFIG_DIR/server.conf" "$SERVERS_DIR/$server_name/server.conf"
    fi
    
    # Update port in config
    sed -i "s/^port 1194/port $server_port/" "$SERVERS_DIR/$server_name/server.conf"
    
    # Create server info file
    cat > "$SERVERS_DIR/$server_name/info.json" <<EOF
{
    "name": "$server_name",
    "ip": "$server_ip",
    "port": $server_port,
    "location": "$server_location",
    "status": "active",
    "load": 0,
    "latency": 0
}
EOF
    
    # Create systemd service
    cat > "/etc/systemd/system/phaze-vpn-$server_name.service" <<EOF
[Unit]
Description=PhazeVPN Server - $server_name
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/openvpn --config $SERVERS_DIR/$server_name/server.conf
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    
    echo "✅ Server $server_name configured"
    echo ""
}

# Function to start all servers
start_all_servers() {
    echo "Starting all VPN servers..."
    for server_dir in "$SERVERS_DIR"/*; do
        if [ -d "$server_dir" ]; then
            server_name=$(basename "$server_dir")
            echo "Starting $server_name..."
            systemctl enable "phaze-vpn-$server_name.service"
            systemctl start "phaze-vpn-$server_name.service"
        fi
    done
    echo "✅ All servers started"
}

# Function to create load balancer config
create_load_balancer() {
    echo "Creating load balancer configuration..."
    
    cat > "$SCRIPTS_DIR/load-balancer.py" <<'PYTHON_EOF'
#!/usr/bin/env python3
"""
PhazeVPN Load Balancer
Routes clients to best server based on latency and load
"""
import json
import os
import subprocess
import socket
import time
from pathlib import Path

SERVERS_DIR = Path('/opt/phaze-vpn/servers')
CONFIG_DIR = Path('/opt/phaze-vpn/config')

def ping_server(ip):
    """Ping server and return latency in ms"""
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '1', ip],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            # Parse ping output
            output = result.stdout.decode()
            for line in output.split('\n'):
                if 'time=' in line:
                    latency = float(line.split('time=')[1].split()[0])
                    return latency
    except:
        pass
    return None

def get_server_load(server_name):
    """Get current load of server"""
    try:
        status_file = Path(f'/tmp/openvpn-status-{server_name}.log')
        if status_file.exists():
            # Count connected clients
            with open(status_file) as f:
                content = f.read()
                return content.count('CLIENT_LIST')
    except:
        pass
    return 0

def get_best_server():
    """Get best server based on latency and load"""
    servers = []
    
    for server_dir in SERVERS_DIR.iterdir():
        if not server_dir.is_dir():
            continue
            
        info_file = server_dir / 'info.json'
        if not info_file.exists():
            continue
            
        with open(info_file) as f:
            info = json.load(f)
        
        if info.get('status') != 'active':
            continue
        
        # Ping server
        latency = ping_server(info['ip'])
        if latency is None:
            continue
        
        # Get load
        load = get_server_load(info['name'])
        
        # Calculate score (lower is better)
        # Latency weight: 70%, Load weight: 30%
        score = (latency * 0.7) + (load * 0.3)
        
        servers.append({
            'name': info['name'],
            'ip': info['ip'],
            'port': info['port'],
            'latency': latency,
            'load': load,
            'score': score
        })
    
    if not servers:
        return None
    
    # Sort by score
    servers.sort(key=lambda x: x['score'])
    return servers[0]

if __name__ == '__main__':
    best = get_best_server()
    if best:
        print(json.dumps(best, indent=2))
    else:
        print('{"error": "No servers available"}')
PYTHON_EOF
    
    chmod +x "$SCRIPTS_DIR/load-balancer.py"
    echo "✅ Load balancer created"
}

# Main menu
if [ "$1" == "add" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "Usage: $0 add <server_name> <server_ip> [port] [location]"
        exit 1
    fi
    add_server_ip "$2" "$3" "${4:-1194}" "${5:-Unknown}"
elif [ "$1" == "start" ]; then
    start_all_servers
elif [ "$1" == "load-balancer" ]; then
    create_load_balancer
else
    echo "Usage: $0 {add|start|load-balancer}"
    echo ""
    echo "Examples:"
    echo "  $0 add us-east 192.168.1.100 1194 'New York'"
    echo "  $0 add us-west 192.168.1.101 1194 'Los Angeles'"
    echo "  $0 add eu 192.168.1.102 1194 'London'"
    echo "  $0 start"
    echo "  $0 load-balancer"
fi

