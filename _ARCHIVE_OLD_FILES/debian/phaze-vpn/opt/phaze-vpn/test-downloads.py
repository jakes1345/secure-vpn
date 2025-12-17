#!/usr/bin/env python3
"""
Test download functionality for all platforms
"""

import requests
import sys
from pathlib import Path

BASE_URL = "https://phazevpn.duckdns.org"

print("=" * 70)
print("🧪 TESTING DOWNLOAD FUNCTIONALITY")
print("=" * 70)
print("")

# Test each platform
platforms = ['windows', 'linux', 'macos']
results = {}

for platform in platforms:
    print(f"Testing {platform.upper()} download...")
    url = f"{BASE_URL}/download/client/{platform}"
    
    try:
        response = requests.get(url, stream=True, timeout=10, verify=False)
        
        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', '0')
            
            # Check filename
            content_disposition = response.headers.get('Content-Disposition', '')
            
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📦 Content-Type: {content_type}")
            print(f"   📏 Size: {content_length} bytes")
            print(f"   📄 Disposition: {content_disposition}")
            
            # Download first few bytes to verify
            chunk = next(response.iter_content(1024), b'')
            if chunk:
                print(f"   ✅ File content received ({len(chunk)} bytes)")
                results[platform] = {
                    'status': 'SUCCESS',
                    'content_type': content_type,
                    'size': content_length,
                    'has_content': True
                }
            else:
                print(f"   ⚠️  No content received")
                results[platform] = {'status': 'NO_CONTENT'}
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            results[platform] = {'status': 'FAILED', 'code': response.status_code}
            
    except requests.exceptions.SSLError:
        # Try without SSL verification
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, stream=True, timeout=10, verify=False)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                print(f"   ✅ Status: {response.status_code} (SSL warning ignored)")
                print(f"   📦 Content-Type: {content_type}")
                results[platform] = {'status': 'SUCCESS', 'content_type': content_type}
            else:
                print(f"   ❌ Status: {response.status_code}")
                results[platform] = {'status': 'FAILED', 'code': response.status_code}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[platform] = {'status': 'ERROR', 'error': str(e)}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results[platform] = {'status': 'ERROR', 'error': str(e)}
    
    print("")

print("=" * 70)
print("📊 TEST RESULTS SUMMARY")
print("=" * 70)
print("")

for platform, result in results.items():
    status = result.get('status', 'UNKNOWN')
    icon = '✅' if status == 'SUCCESS' else '❌'
    print(f"{icon} {platform.upper()}: {status}")
    if 'content_type' in result:
        print(f"   Type: {result['content_type']}")
    if 'error' in result:
        print(f"   Error: {result['error']}")

print("")
print("=" * 70)

# Check local files
print("")
print("📁 Checking local installer files...")
print("")

BASE_DIR = Path(__file__).parent
installer_paths = {
    'windows': BASE_DIR / 'phazevpn-client' / 'installers' / 'phazevpn-client-windows.zip',
    'linux': BASE_DIR / 'phazevpn-client' / 'installers' / 'phazevpn-client-linux.tar.gz',
    'macos': BASE_DIR / 'phazevpn-client' / 'installers' / 'phazevpn-client-macos.tar.gz'
}

for platform, path in installer_paths.items():
    if path.exists():
        size = path.stat().st_size
        print(f"   ✅ {platform.upper()}: {path.name} ({size:,} bytes)")
    else:
        print(f"   ❌ {platform.upper()}: {path.name} NOT FOUND")

print("")

