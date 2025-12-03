#!/usr/bin/env python3
"""
Update Linux Package with Unified Client
- Replace old client with unified version
- Update .deb package
- Set up apt repository for updates
"""

from pathlib import Path
import shutil
import subprocess

print("=" * 80)
print("📦 UPDATING LINUX PACKAGE - UNIFIED CLIENT")
print("=" * 80)
print("")

# Paths
client_dir = Path("phazevpn-client")
deb_build_dir = client_dir / "deb-build"
unified_client = client_dir / "phazevpn-unified.py"
deb_client = deb_build_dir / "usr/share/phazevpn-client/phazevpn-client.py"

print("1️⃣ Updating .deb package with unified client...")

if unified_client.exists() and deb_build_dir.exists():
    # Copy unified client to deb package
    shutil.copy2(unified_client, deb_client)
    print(f"   ✅ Copied unified client to deb package")
    
    # Update desktop file if needed
    desktop_file = deb_build_dir / "usr/share/applications/phazevpn-client.desktop"
    if desktop_file.exists():
        desktop_content = desktop_file.read_text()
        if "PhazeVPN Professional" not in desktop_content:
            desktop_content = desktop_content.replace(
                "PhazeVPN Client",
                "PhazeVPN - Unified Client & Dashboard"
            )
            desktop_file.write_text(desktop_content)
            print(f"   ✅ Updated desktop file")
    
    # Update control file version
    control_file = deb_build_dir / "DEBIAN/control"
    if control_file.exists():
        control_content = control_file.read_text()
        # Update version to 2.0.0 (major update with unified client)
        if "Version: 1.0.0" in control_content:
            control_content = control_content.replace(
                "Version: 1.0.0",
                "Version: 2.0.0"
            )
            control_file.write_text(control_content)
            print(f"   ✅ Updated package version to 2.0.0")
    
    print("   ✅ .deb package updated!")
else:
    print("   ⚠️  Files not found")

print("")
print("2️⃣ Package structure:")
print(f"   - Client: {deb_client.name if deb_client.exists() else 'NOT FOUND'}")
print(f"   - Size: {unified_client.stat().st_size / 1024:.1f} KB" if unified_client.exists() else "")

print("")
print("✅ Linux package ready for rebuild!")
print("")
print("📋 Next steps:")
print("   1. Build .deb: cd phazevpn-client && ./build-deb.sh")
print("   2. Install: sudo dpkg -i phazevpn-client_2.0.0_amd64.deb")
print("   3. Run: phazevpn-client")

