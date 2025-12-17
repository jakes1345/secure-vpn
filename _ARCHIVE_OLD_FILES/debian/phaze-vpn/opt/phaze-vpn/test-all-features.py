#!/usr/bin/env python3
"""
Test All Deployed Features
Quick verification that everything is working
"""

import requests
import sys

VPS_HOST = "15.204.11.19"

def test_endpoint(url, name):
    """Test an API endpoint"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"   ✅ {name}: OK")
            return True
        else:
            print(f"   ⚠️  {name}: Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ {name}: Connection failed")
        return False
    except Exception as e:
        print(f"   ❌ {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 Testing All Deployed Features")
    print("=" * 60)
    
    results = []
    
    # Email API
    print("\n📧 Email API (Port 5001):")
    results.append(test_endpoint(
        f"http://{VPS_HOST}:5001/api/v1/health",
        "Health Check"
    ))
    
    # File Storage API
    print("\n📁 File Storage API (Port 5002):")
    results.append(test_endpoint(
        f"http://{VPS_HOST}:5002/api/v1/storage/health",
        "Health Check"
    ))
    
    # Productivity API
    print("\n📝 Productivity Suite API (Port 5003):")
    results.append(test_endpoint(
        f"http://{VPS_HOST}:5003/api/v1/productivity/health",
        "Health Check"
    ))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All services are running correctly!")
    else:
        print(f"\n⚠️  {total - passed} service(s) need attention")
    
    print("\n📋 Services:")
    print("   - Email API: http://15.204.11.19:5001")
    print("   - File Storage: http://15.204.11.19:5002")
    print("   - Productivity: http://15.204.11.19:5003")
    print("   - Calendar/Contacts: Port 5232")

if __name__ == "__main__":
    main()
