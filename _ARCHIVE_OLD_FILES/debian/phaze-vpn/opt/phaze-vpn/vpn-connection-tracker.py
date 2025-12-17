#!/usr/bin/env python3
"""
Real-time VPN Connection Tracker
Monitors OpenVPN connections and logs activity
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import sys

VPN_DIR = Path('/opt/secure-vpn')
STATUS_LOG = VPN_DIR / 'logs' / 'status.log'
CONNECTION_LOG = VPN_DIR / 'logs' / 'connection-tracker.json'
CONNECTION_HISTORY = VPN_DIR / 'logs' / 'connection-history.json'

def get_active_connections():
    """Parse OpenVPN status log and get active connections"""
    connections = []
    if not STATUS_LOG.exists():
        return connections
    
    try:
        with open(STATUS_LOG, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and line[0].isdigit():
                    parts = line.split(',')
                    if len(parts) >= 6:
                        connections.append({
                            'virtual_ip': parts[0],
                            'name': parts[1] if len(parts) > 1 else 'Unknown',
                            'real_ip': parts[2] if len(parts) > 2 else 'N/A',
                            'bytes_rx': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
                            'bytes_tx': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                            'connected_since': parts[5] if len(parts) > 5 else 'N/A',
                            'last_seen': datetime.now().isoformat()
                        })
    except Exception as e:
        print(f"Error reading status log: {e}")
    
    return connections

def load_connection_log():
    """Load connection tracking log"""
    if CONNECTION_LOG.exists():
        try:
            with open(CONNECTION_LOG, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'last_check': None,
        'current_connections': {},
        'total_connections': 0,
        'total_data': {'rx': 0, 'tx': 0}
    }

def save_connection_log(data):
    """Save connection tracking log"""
    CONNECTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CONNECTION_LOG, 'w') as f:
        json.dump(data, f, indent=2)

def update_connection_history(connections):
    """Update connection history file"""
    CONNECTION_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing history
    history = []
    if CONNECTION_HISTORY.exists():
        try:
            with open(CONNECTION_HISTORY, 'r') as f:
                history = json.load(f)
        except:
            pass
    
    # Load previous state
    log_data = load_connection_log()
    previous = log_data.get('current_connections', {})
    
    current_names = {c.get('name', 'Unknown') for c in connections}
    previous_names = set(previous.keys())
    
    # Detect new connections
    for conn in connections:
        name = conn.get('name', 'Unknown')
        if name not in previous_names:
            history.append({
                'name': name,
                'virtual_ip': conn.get('virtual_ip', 'N/A'),
                'real_ip': conn.get('real_ip', 'N/A'),
                'action': 'connected',
                'timestamp': datetime.now().isoformat()
            })
            print(f"🟢 NEW CONNECTION: {name} ({conn.get('real_ip', 'N/A')})")
    
    # Detect disconnections
    for name in previous_names:
        if name not in current_names:
            history.append({
                'name': name,
                'action': 'disconnected',
                'timestamp': datetime.now().isoformat()
            })
            print(f"🔴 DISCONNECTED: {name}")
    
    # Keep last 1000 entries
    history = history[-1000:]
    
    with open(CONNECTION_HISTORY, 'w') as f:
        json.dump(history, f, indent=2)

def format_bytes(bytes_val):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def track_connections():
    """Main tracking loop"""
    print("="*60)
    print("🔒 VPN Connection Tracker Started")
    print("="*60)
    print(f"Status log: {STATUS_LOG}")
    print(f"Tracking log: {CONNECTION_LOG}")
    print("="*60)
    print()
    
    last_connections = {}
    
    while True:
        try:
            # Get current connections
            connections = get_active_connections()
            
            # Update connection history
            if connections != last_connections:
                update_connection_history(connections)
                last_connections = {c.get('name'): c for c in connections}
            
            # Build tracking data
            current_map = {c.get('name', 'Unknown'): c for c in connections}
            
            log_data = load_connection_log()
            log_data['last_check'] = datetime.now().isoformat()
            log_data['current_connections'] = current_map
            
            # Calculate totals
            total_rx = sum(c.get('bytes_rx', 0) for c in connections)
            total_tx = sum(c.get('bytes_tx', 0) for c in connections)
            log_data['total_data'] = {'rx': total_rx, 'tx': total_tx}
            log_data['total_connections'] = len(connections)
            
            # Save tracking log
            save_connection_log(log_data)
            
            # Display status
            if connections:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Active: {len(connections)} client(s)")
                for conn in connections:
                    name = conn.get('name', 'Unknown')
                    rx = conn.get('bytes_rx', 0)
                    tx = conn.get('bytes_tx', 0)
                    total = rx + tx
                    print(f"  • {name:20s} | {conn.get('real_ip', 'N/A'):15s} | Total: {format_bytes(total)}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No active connections")
            
            # Wait before next check
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\nTracker stopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    track_connections()

