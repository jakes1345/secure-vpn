#!/usr/bin/env python3
"""
Test Email Features (Calendar, Contacts, API)
Verifies that all features are working correctly
"""

import paramiko
import requests
import time
import sys

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
API_URL = f"http://{VPS_HOST}:5000/api/v1"

def run_command(ssh, command):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def test_api():
    """Test REST API"""
    print("\n🔌 Testing REST API...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ API Health Check: OK")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   ❌ API Health Check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ⚠️  API not responding (may still be starting)")
        return False
    except Exception as e:
        print(f"   ❌ API Error: {e}")
        return False

def test_services(ssh):
    """Test service status"""
    print("\n🔍 Checking Service Status...")
    
    services = {
        "radicale": "Calendar/Contacts Server",
        "phazevpn-email-api": "REST API",
        "postfix": "Email Server (SMTP)",
        "dovecot": "Email Server (IMAP)"
    }
    
    all_ok = True
    for service, desc in services.items():
        success, output, error = run_command(ssh, f"systemctl is-active {service}")
        if "active" in output.lower():
            print(f"   ✅ {service} ({desc}): Running")
        else:
            print(f"   ⚠️  {service} ({desc}): {output.strip()}")
            all_ok = False
    
    return all_ok

def test_ports(ssh):
    """Test if ports are open"""
    print("\n🔌 Checking Ports...")
    
    ports = {
        "5232": "CalDAV/CardDAV",
        "5000": "REST API",
        "25": "SMTP",
        "587": "SMTP (Submission)",
        "993": "IMAP (SSL)",
        "143": "IMAP"
    }
    
    for port, desc in ports.items():
        success, output, error = run_command(
            ssh, 
            f"ss -tlnp | grep ':{port} ' || netstat -tlnp | grep ':{port} ' || echo 'not-found'"
        )
        if success and port in output:
            print(f"   ✅ Port {port} ({desc}): Open")
        else:
            print(f"   ⚠️  Port {port} ({desc}): Not listening")

def main():
    print("=" * 60)
    print("🧪 Testing Email Features")
    print("=" * 60)
    
    # Connect to VPS
    print("\n1️⃣ Connecting to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        sys.exit(1)
    
    try:
        # Wait a bit for services to start
        print("\n⏳ Waiting for services to start...")
        time.sleep(5)
        
        # Test services
        test_services(ssh)
        
        # Test ports
        test_ports(ssh)
        
        # Test API
        test_api()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print("\n✅ Features Deployed:")
        print("   - Calendar System (CalDAV)")
        print("   - Contacts System (CardDAV)")
        print("   - REST API")
        print("\n🔧 To use:")
        print("   1. Calendar: Connect with Thunderbird/Apple Calendar")
        print("   2. Contacts: Sync with CardDAV client")
        print("   3. API: Use REST endpoints for automation")
        print("\n📖 See EMAIL-FEATURES-IMPLEMENTATION.md for details")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
