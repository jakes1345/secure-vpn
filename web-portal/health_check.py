#!/usr/bin/env python3
"""
Health Check Module
Provides health check endpoints for monitoring and status checks
"""

from flask import jsonify
from datetime import datetime
import os
from pathlib import Path

def check_database_health():
    """
    Check database connection health.
    
    Returns:
        dict: Health status with details
    """
    try:
        from mysql_db import get_connection, init_database
        
        # Test connection
        if not init_database():
            return {
                'status': 'unhealthy',
                'error': 'Database connection failed',
                'timestamp': datetime.now().isoformat()
            }
        
        # Test query
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def check_disk_space():
    """
    Check disk space availability.
    
    Returns:
        dict: Disk space status
    """
    try:
        import shutil
        
        # Check root filesystem
        total, used, free = shutil.disk_usage('/')
        
        # Calculate percentages
        used_percent = (used / total) * 100
        free_percent = (free / total) * 100
        
        status = 'healthy'
        if used_percent > 90:
            status = 'critical'
        elif used_percent > 80:
            status = 'warning'
        
        return {
            'status': status,
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'used_percent': round(used_percent, 2),
            'free_percent': round(free_percent, 2),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unknown',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def check_vpn_service():
    """
    Check VPN service status.
    
    Returns:
        dict: VPN service status
    """
    try:
        import subprocess
        
        # Check if OpenVPN is running
        result = subprocess.run(
            ['systemctl', 'is-active', 'openvpn@server'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        is_active = result.returncode == 0 and 'active' in result.stdout.lower()
        
        return {
            'status': 'healthy' if is_active else 'unhealthy',
            'service': 'openvpn@server',
            'active': is_active,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unknown',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def check_web_portal():
    """
    Check web portal status.
    
    Returns:
        dict: Web portal status
    """
    try:
        # Check if required directories exist
        base_dir = Path(__file__).parent.parent
        required_dirs = [
            base_dir / 'web-portal',
            base_dir / 'web-portal' / 'templates',
            base_dir / 'web-portal' / 'static',
        ]
        
        missing_dirs = [str(d) for d in required_dirs if not d.exists()]
        
        if missing_dirs:
            return {
                'status': 'unhealthy',
                'error': f'Missing directories: {", ".join(missing_dirs)}',
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_system_info():
    """
    Get system information (non-sensitive).
    
    Returns:
        dict: System information
    """
    try:
        import platform
        
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def comprehensive_health_check():
    """
    Perform comprehensive health check of all services.
    
    Returns:
        dict: Complete health status
    """
    checks = {
        'database': check_database_health(),
        'disk_space': check_disk_space(),
        'vpn_service': check_vpn_service(),
        'web_portal': check_web_portal(),
        'system': get_system_info(),
    }
    
    # Overall status
    unhealthy_count = sum(1 for check in checks.values() if check.get('status') == 'unhealthy')
    warning_count = sum(1 for check in checks.values() if check.get('status') == 'warning')
    
    if unhealthy_count > 0:
        overall_status = 'unhealthy'
    elif warning_count > 0:
        overall_status = 'degraded'
    else:
        overall_status = 'healthy'
    
    return {
        'status': overall_status,
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }
