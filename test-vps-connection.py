#!/usr/bin/env python3
"""
Quick test script to verify VPS connection
"""

import paramiko
import os
from pathlib import Path

VPS_HOST = '15.204.11.19'
VPS_USER = 'root'
VPS_PASSWORD = 'Jakes1328!@'

def test_connection():
    """Test SSH connection to VPS"""
    print("=" * 60)
    print("🔍 Testing VPS Connection")
    print("=" * 60)
    print(f"Host: {VPS_USER}@{VPS_HOST}")
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("📡 Connecting...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        print("   ✅ Connected successfully!")
        print()
        
        # Test a simple command
        print("🔍 Testing commands...")
        stdin, stdout, stderr = ssh.exec_command("uname -a")
        output = stdout.read().decode().strip()
        print(f"   System: {output}")
        
        stdin, stdout, stderr = ssh.exec_command("pwd")
        output = stdout.read().decode().strip()
        print(f"   Current dir: {output}")
        
        stdin, stdout, stderr = ssh.exec_command("which cmake go python3")
        output = stdout.read().decode().strip()
        print(f"   Tools: {output}")
        
        print()
        print("=" * 60)
        print("✅ Connection test successful!")
        print("=" * 60)
        print()
        print("Ready to deploy! Run:")
        print("   python3 deploy-cmake-to-vps.py")
        print()
        
        return True
        
    except paramiko.AuthenticationException:
        print("   ❌ Authentication failed - check password")
        return False
    except paramiko.SSHException as e:
        print(f"   ❌ SSH error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    finally:
        ssh.close()

if __name__ == '__main__':
    test_connection()

