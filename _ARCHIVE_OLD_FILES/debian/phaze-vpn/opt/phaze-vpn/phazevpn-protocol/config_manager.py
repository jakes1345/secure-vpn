#!/usr/bin/env python3
"""
PhazeVPN Protocol - Configuration Management
Easy server configuration with YAML/JSON
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Optional, Any

class ConfigManager:
    """
    Manages server configuration
    """
    
    def __init__(self, config_file: str = '/etc/phazevpn/config.yaml'):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.defaults = self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 51820,
                'vpn_network': '10.9.0.0/24',
                'server_ip': '10.9.0.1',
                'max_clients': 1000,
                'connection_timeout': 120
            },
            'security': {
                'zero_knowledge': True,
                'enable_compression': True,
                'enable_obfuscation': True,
                'perfect_forward_secrecy': True,
                'rekey_bytes': 100 * 1024 * 1024,  # 100MB
                'rekey_time': 3600,  # 1 hour
                'enable_replay_protection': True
            },
            'performance': {
                'compression_level': 6,
                'compression_min_size': 100,
                'compression_algorithm': 'zlib',
                'enable_async': True,
                'worker_threads': 4
            },
            'network': {
                'enable_nat_traversal': True,
                'stun_servers': [
                    'stun.stunprotocol.org:3478',
                    'stun.l.google.com:19302'
                ],
                'enable_ipv6': False
            },
            'rate_limiting': {
                'enabled': True,
                'default_limit_bytes_per_sec': 10 * 1024 * 1024,  # 10MB/s
                'burst_size': 50 * 1024 * 1024,  # 50MB
                'max_connections_per_user': 5
            },
            'split_tunneling': {
                'enabled': False,
                'vpn_routes': [],
                'exclude_routes': []
            },
            'logging': {
                'level': 'ERROR',  # Only errors
                'log_traffic': False,
                'log_connections': False,
                'log_users': False
            }
        }
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            # Create default config
            self.config = self.defaults.copy()
            self.save()
            return self.config
        
        try:
            if self.config_file.suffix == '.yaml' or self.config_file.suffix == '.yml':
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            
            # Merge with defaults
            self.config = self._merge_dicts(self.defaults, self.config)
            
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            self.config = self.defaults.copy()
        
        return self.config
    
    def save(self):
        """Save configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.config_file.suffix == '.yaml' or self.config_file.suffix == '.yml':
                with open(self.config_file, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-separated path
        Example: get('server.port') -> 51820
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set config value by dot-separated path
        Example: set('server.port', 51821)
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def _merge_dicts(self, base: Dict, override: Dict) -> Dict:
        """Merge two dictionaries recursively"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result

