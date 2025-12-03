#!/usr/bin/env python3
"""
PhazeVPN Protocol - Packet Compression
30-50% bandwidth savings
"""

import zlib
import lz4.frame
import os

class PacketCompressor:
    """
    Compress VPN packets to save bandwidth
    Only compresses if it saves space (no overhead for small packets)
    """
    
    def __init__(self, compression_level=6, min_size=100, algorithm='zlib'):
        """
        Args:
            compression_level: 1-9 (higher = better compression, slower)
            min_size: Only compress packets larger than this (bytes)
            algorithm: 'zlib' or 'lz4' (lz4 is faster, zlib compresses better)
        """
        self.compression_level = compression_level
        self.min_size = min_size
        self.algorithm = algorithm
        self.compress_count = 0
        self.uncompress_count = 0
        self.bytes_saved = 0
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress packet if it's worth it
        Returns compressed data with header, or original if not compressed
        """
        # Don't compress small packets (overhead not worth it)
        if len(data) < self.min_size:
            return data
        
        try:
            if self.algorithm == 'zlib':
                compressed = zlib.compress(data, level=self.compression_level)
            elif self.algorithm == 'lz4':
                compressed = lz4.frame.compress(data, compression_level=self.compression_level)
            else:
                return data
            
            # Only use compression if it saves space
            # Add 1 byte header: 0x01 = compressed, 0x00 = not compressed
            if len(compressed) < len(data) - 1:  # -1 for header overhead
                self.compress_count += 1
                self.bytes_saved += len(data) - len(compressed) - 1
                return b'\x01' + compressed  # Header + compressed data
            else:
                return b'\x00' + data  # Header + original data
        
        except Exception:
            # If compression fails, return original
            return b'\x00' + data
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress packet if it was compressed
        """
        if len(data) < 1:
            return data
        
        header = data[0]
        payload = data[1:]
        
        if header == 0x01:  # Compressed
            try:
                if self.algorithm == 'zlib':
                    decompressed = zlib.decompress(payload)
                elif self.algorithm == 'lz4':
                    decompressed = lz4.frame.decompress(payload)
                else:
                    return payload
                
                self.uncompress_count += 1
                return decompressed
            
            except Exception:
                return payload  # Return as-is if decompression fails
        
        elif header == 0x00:  # Not compressed
            return payload
        
        else:
            # Unknown header, return as-is
            return data
    
    def get_stats(self) -> dict:
        """Get compression statistics"""
        return {
            'compressed_packets': self.compress_count,
            'decompressed_packets': self.uncompress_count,
            'bytes_saved': self.bytes_saved,
            'compression_ratio': (self.bytes_saved / max(1, self.compress_count * 1024)) * 100 if self.compress_count > 0 else 0
        }

class AdaptiveCompressor:
    """
    Automatically adjusts compression based on network conditions
    """
    
    def __init__(self):
        self.zlib_compressor = PacketCompressor(algorithm='zlib', compression_level=6)
        self.lz4_compressor = PacketCompressor(algorithm='lz4', compression_level=4)
        self.current_algorithm = 'zlib'
        self.performance_history = []
    
    def compress(self, data: bytes) -> bytes:
        """Compress using current best algorithm"""
        if self.current_algorithm == 'zlib':
            return self.zlib_compressor.compress(data)
        else:
            return self.lz4_compressor.compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress using current algorithm"""
        if self.current_algorithm == 'zlib':
            return self.zlib_compressor.decompress(data)
        else:
            return self.lz4_compressor.decompress(data)
    
    def adapt(self, latency_ms: float, cpu_usage: float):
        """
        Adapt compression based on network conditions
        - High latency: Use better compression (zlib)
        - Low latency, high CPU: Use faster compression (lz4)
        """
        if latency_ms > 100 and cpu_usage < 50:
            self.current_algorithm = 'zlib'  # Better compression
        elif latency_ms < 50 and cpu_usage > 70:
            self.current_algorithm = 'lz4'  # Faster compression

