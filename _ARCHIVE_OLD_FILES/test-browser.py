#!/usr/bin/env python3
"""
Test script to verify browser dependencies and functionality
"""
import sys
import subprocess

def check_dependency(name, check_cmd, install_cmd):
    """Check if a dependency is installed"""
    print(f"\n🔍 Checking {name}...")
    try:
        result = subprocess.run(check_cmd, shell=True, 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✅ {name} is installed")
            return True
        else:
            print(f"   ❌ {name} is NOT installed")
            print(f"   Install with: {install_cmd}")
            return False
    except Exception as e:
        print(f"   ⚠️  Error checking {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("PhazeBrowser Dependency Check")
    print("=" * 60)
    
    all_ok = True
    
    # Check Python version
    print(f"\n🐍 Python version: {sys.version}")
    if sys.version_info < (3, 6):
        print("   ❌ Python 3.6+ required")
        all_ok = False
    else:
        print("   ✅ Python version OK")
    
    # Check GTK3
    all_ok &= check_dependency(
        "GTK3",
        "python3 -c 'import gi; gi.require_version(\"Gtk\", \"3.0\"); from gi.repository import Gtk; print(\"OK\")'",
        "sudo apt-get install python3-gi gir1.2-gtk-3.0"
    )
    
    # Check WebKit2
    all_ok &= check_dependency(
        "WebKit2",
        "python3 -c 'import gi; gi.require_version(\"WebKit2\", \"4.1\"); from gi.repository import WebKit2; print(\"OK\")'",
        "sudo apt-get install gir1.2-webkit2-4.1"
    )
    
    # Check VPN tools
    all_ok &= check_dependency(
        "ip command",
        "which ip",
        "sudo apt-get install iproute2"
    )
    
    # Check OpenVPN
    check_dependency(
        "OpenVPN",
        "which openvpn",
        "sudo apt-get install openvpn"
    )
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All critical dependencies are installed!")
        print("   You can run: python3 phazebrowser.py")
    else:
        print("❌ Some dependencies are missing")
        print("   Install missing dependencies and try again")
    print("=" * 60)

if __name__ == "__main__":
    main()

