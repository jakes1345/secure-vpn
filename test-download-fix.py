#!/usr/bin/env python3
"""
Test download server to verify downloads work
"""

import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
CLIENT_CONFIGS_DIR = BASE_DIR / 'client-configs'

print("="*70)
print("🔍 TESTING DOWNLOAD SERVER")
print("="*70)
print("")

# Check if configs exist
if not CLIENT_CONFIGS_DIR.exists():
    print(f"❌ Config directory not found: {CLIENT_CONFIGS_DIR}")
    print(f"   Creating directory...")
    CLIENT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"   ✅ Created")
else:
    print(f"✅ Config directory exists: {CLIENT_CONFIGS_DIR}")

# List available configs
configs = list(CLIENT_CONFIGS_DIR.glob('*.ovpn'))
print(f"📁 Available configs: {len(configs)}")
for config in configs[:5]:
    print(f"   - {config.name} ({config.stat().st_size} bytes)")

if not configs:
    print("⚠️  No config files found!")
    print("   Create a client config first:")
    print("   python3 vpn-manager.py add-client test-client")
    print("")
else:
    # Test download for first config
    test_client = configs[0].stem
    print("")
    print(f"🧪 Testing download for: {test_client}")
    print("")
    
    # Test URL
    test_url = f"http://localhost:8081/download?name={test_client}&type=openvpn"
    print(f"   URL: {test_url}")
    
    try:
        response = requests.get(test_url, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Headers:")
        for key, value in response.headers.items():
            if 'content' in key.lower() or 'disposition' in key.lower():
                print(f"      {key}: {value}")
        
        if response.status_code == 200:
            print(f"   ✅ Download works! Content length: {len(response.content)} bytes")
            print(f"   First 100 chars: {response.text[:100]}")
        else:
            print(f"   ❌ Download failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Download server not running!")
        print("   Start it with: python3 client-download-server.py")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("")
print("="*70)
print("✅ TEST COMPLETE")
print("="*70)
print("")
print("If downloads don't work:")
print("  1. Make sure download server is running")
print("  2. Check browser console for errors")
print("  3. Try direct URL: http://localhost:8081/download?name=CLIENT_NAME&type=openvpn")
print("")


