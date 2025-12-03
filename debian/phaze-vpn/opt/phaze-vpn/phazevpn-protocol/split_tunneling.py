#!/usr/bin/env python3
"""
PhazeVPN Protocol - Split Tunneling
Route only specific traffic through VPN, rest goes direct
"""

import ipaddress
import socket
from typing import List, Optional, Tuple

class SplitTunnelManager:
    """
    Manages split tunneling rules
    Only routes matching traffic through VPN
    """
    
    def __init__(self, rules: List[str] = None):
        """
        Args:
            rules: List of CIDR ranges or domains to route through VPN
                   Example: ['10.0.0.0/8', '192.168.1.0/24', 'example.com']
        """
        self.vpn_routes = []  # CIDR networks to route through VPN
        self.vpn_domains = []  # Domains to route through VPN
        self.exclude_routes = []  # Networks to exclude from VPN
        self.enabled = False
        
        if rules:
            self.add_rules(rules)
    
    def add_rule(self, rule: str):
        """Add a routing rule (CIDR or domain)"""
        rule = rule.strip()
        
        if '/' in rule:  # CIDR notation
            try:
                network = ipaddress.ip_network(rule, strict=False)
                if rule not in self.vpn_routes:
                    self.vpn_routes.append(rule)
            except ValueError:
                pass
        elif rule.startswith('!'):  # Exclude rule
            exclude = rule[1:].strip()
            if '/' in exclude:
                try:
                    network = ipaddress.ip_network(exclude, strict=False)
                    if exclude not in self.exclude_routes:
                        self.exclude_routes.append(exclude)
                except ValueError:
                    pass
        else:  # Domain name
            if rule not in self.vpn_domains:
                self.vpn_domains.append(rule)
    
    def add_rules(self, rules: List[str]):
        """Add multiple rules"""
        for rule in rules:
            self.add_rule(rule)
    
    def should_route_through_vpn(self, ip_address: str, domain: str = None) -> bool:
        """
        Determine if traffic should go through VPN
        Returns True if should use VPN, False for direct connection
        """
        if not self.enabled:
            return True  # Route everything through VPN by default
        
        try:
            ip = ipaddress.ip_address(ip_address)
        except ValueError:
            return True  # Default to VPN if IP invalid
        
        # Check exclude rules first
        for exclude_net in self.exclude_routes:
            try:
                network = ipaddress.ip_network(exclude_net, strict=False)
                if ip in network:
                    return False  # Explicitly excluded
            except ValueError:
                continue
        
        # Check VPN routes
        for vpn_net in self.vpn_routes:
            try:
                network = ipaddress.ip_network(vpn_net, strict=False)
                if ip in network:
                    return True  # Match - use VPN
            except ValueError:
                continue
        
        # Check domains
        if domain:
            for vpn_domain in self.vpn_domains:
                if domain == vpn_domain or domain.endswith('.' + vpn_domain):
                    return True  # Match - use VPN
        
        # Default: use VPN if rules specified, otherwise use VPN for everything
        return len(self.vpn_routes) == 0 and len(self.vpn_domains) == 0
    
    def resolve_domain(self, domain: str) -> Optional[str]:
        """Resolve domain to IP address"""
        try:
            ip = socket.gethostbyname(domain)
            return ip
        except socket.gaierror:
            return None
    
    def enable(self):
        """Enable split tunneling"""
        self.enabled = True
    
    def disable(self):
        """Disable split tunneling (route everything through VPN)"""
        self.enabled = False
    
    def get_rules(self) -> dict:
        """Get current rules"""
        return {
            'enabled': self.enabled,
            'vpn_routes': self.vpn_routes,
            'vpn_domains': self.vpn_domains,
            'exclude_routes': self.exclude_routes
        }

