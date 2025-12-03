#!/usr/bin/env python3
"""
PhazeVPN Protocol - Connection Statistics
Privacy-preserving aggregate statistics only
"""

import time
from collections import deque
from typing import Dict, Optional
import statistics

class ConnectionStatistics:
    """
    Aggregate statistics for server monitoring
    NO individual user tracking
    """
    
    def __init__(self):
        self.start_time = time.time()
        
        # Aggregate stats only
        self.total_connections = 0
        self.active_connections = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        self.total_packets_sent = 0
        self.total_packets_received = 0
        
        # Recent samples (for averages)
        self.latency_samples = deque(maxlen=1000)  # Last 1000 latency measurements
        self.packet_loss_samples = deque(maxlen=100)  # Last 100 packet loss measurements
        
        # Network quality metrics
        self.connection_errors = 0
        self.replay_attacks_blocked = 0
        self.rate_limit_hits = 0
    
    def record_connection(self):
        """Record new connection (no user tracking)"""
        self.total_connections += 1
        self.active_connections += 1
    
    def record_disconnection(self):
        """Record disconnection"""
        self.active_connections = max(0, self.active_connections - 1)
    
    def record_traffic(self, bytes_sent: int = 0, bytes_received: int = 0, 
                      packets_sent: int = 0, packets_received: int = 0):
        """Record traffic (aggregate only)"""
        self.total_bytes_sent += bytes_sent
        self.total_bytes_received += bytes_received
        self.total_packets_sent += packets_sent
        self.total_packets_received += packets_received
    
    def record_latency(self, latency_ms: float):
        """Record latency measurement"""
        if 0 < latency_ms < 10000:  # Sanity check
            self.latency_samples.append(latency_ms)
    
    def record_packet_loss(self, loss_percent: float):
        """Record packet loss"""
        if 0 <= loss_percent <= 100:
            self.packet_loss_samples.append(loss_percent)
    
    def record_error(self):
        """Record connection error"""
        self.connection_errors += 1
    
    def record_replay_blocked(self):
        """Record blocked replay attack"""
        self.replay_attacks_blocked += 1
    
    def record_rate_limit_hit(self):
        """Record rate limit hit"""
        self.rate_limit_hits += 1
    
    def get_stats(self) -> Dict:
        """Get aggregate statistics (privacy-preserving)"""
        uptime = time.time() - self.start_time
        
        # Calculate averages
        avg_latency = statistics.mean(self.latency_samples) if self.latency_samples else 0
        avg_packet_loss = statistics.mean(self.packet_loss_samples) if self.packet_loss_samples else 0
        
        # Calculate rates
        bytes_per_sec_sent = self.total_bytes_sent / uptime if uptime > 0 else 0
        bytes_per_sec_received = self.total_bytes_received / uptime if uptime > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'uptime_human': self._format_uptime(uptime),
            'total_connections': self.total_connections,
            'active_connections': self.active_connections,
            'total_bytes_sent': self.total_bytes_sent,
            'total_bytes_received': self.total_bytes_received,
            'total_packets_sent': self.total_packets_sent,
            'total_packets_received': self.total_packets_received,
            'bytes_per_sec_sent': bytes_per_sec_sent,
            'bytes_per_sec_received': bytes_per_sec_received,
            'average_latency_ms': avg_latency,
            'average_packet_loss_percent': avg_packet_loss,
            'connection_errors': self.connection_errors,
            'replay_attacks_blocked': self.replay_attacks_blocked,
            'rate_limit_hits': self.rate_limit_hits
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime as human-readable string"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def reset_stats(self):
        """Reset statistics (keep active connections)"""
        self.total_connections = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        self.total_packets_sent = 0
        self.total_packets_received = 0
        self.latency_samples.clear()
        self.packet_loss_samples.clear()
        self.connection_errors = 0
        self.replay_attacks_blocked = 0
        self.rate_limit_hits = 0

class HealthMonitor:
    """
    Monitor server health
    """
    
    def __init__(self, stats: ConnectionStatistics):
        self.stats = stats
        self.warning_thresholds = {
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85,
            'packet_loss_percent': 5,
            'latency_ms': 200
        }
    
    def check_health(self) -> Dict:
        """Check server health status"""
        stats = self.stats.get_stats()
        
        health = {
            'status': 'healthy',
            'warnings': [],
            'metrics': {}
        }
        
        # Check packet loss
        if stats['average_packet_loss_percent'] > self.warning_thresholds['packet_loss_percent']:
            health['status'] = 'degraded'
            health['warnings'].append(f"High packet loss: {stats['average_packet_loss_percent']:.2f}%")
        
        # Check latency
        if stats['average_latency_ms'] > self.warning_thresholds['latency_ms']:
            health['status'] = 'degraded'
            health['warnings'].append(f"High latency: {stats['average_latency_ms']:.2f}ms")
        
        # Check connection errors
        if self.stats.connection_errors > 100:
            health['status'] = 'degraded'
            health['warnings'].append(f"High error rate: {self.stats.connection_errors} errors")
        
        health['metrics'] = stats
        return health

