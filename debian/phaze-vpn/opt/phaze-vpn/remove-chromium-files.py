#!/usr/bin/env python3
"""
Remove all Chromium-related files since we're using WebKit
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path("/opt/phaze-vpn")

# Files to delete (Chromium-related)
CHROMIUM_FILES = [
    # Chromium build scripts
    "start-chromium-fetch-auto.py",
    "start-chromium-build-final.sh",
    "finish-chromium-build.py",
    "fetch-chromium-properly-vps.py",
    "complete-chromium-fetch.py",
    "check-chromium-structure-vps.py",
    "monitor-chromium-progress.py",
    "move-chromium-to-new-disk.py",
    "optimize-chromium-fetch.sh",
    
    # Chromium status files
    "CHROMIUM-BUILD-COMPLETE.md",
    "CHROMIUM-BUILD-STATUS.md",
    "CHROMIUM-FINAL-STATUS.md",
    "CHROMIUM-READY-SUMMARY.md",
    
    # Chromium in debian package
    "debian/phaze-vpn/opt/phaze-vpn/start-chromium-fetch-auto.py",
    "debian/phaze-vpn/opt/phaze-vpn/start-chromium-build-final.sh",
    "debian/phaze-vpn/opt/phaze-vpn/finish-chromium-build.py",
    "debian/phaze-vpn/opt/phaze-vpn/fetch-chromium-properly-vps.py",
    "debian/phaze-vpn/opt/phaze-vpn/complete-chromium-fetch.py",
    "debian/phaze-vpn/opt/phaze-vpn/check-chromium-structure-vps.py",
    "debian/phaze-vpn/opt/phaze-vpn/monitor-chromium-progress.py",
    "debian/phaze-vpn/opt/phaze-vpn/move-chromium-to-new-disk.py",
    "debian/phaze-vpn/opt/phaze-vpn/optimize-chromium-fetch.sh",
    "debian/phaze-vpn/opt/phaze-vpn/CHROMIUM-BUILD-COMPLETE.md",
    "debian/phaze-vpn/opt/phaze-vpn/CHROMIUM-BUILD-STATUS.md",
    "debian/phaze-vpn/opt/phaze-vpn/CHROMIUM-FINAL-STATUS.md",
    "debian/phaze-vpn/opt/phaze-vpn/CHROMIUM-READY-SUMMARY.md",
    "debian/phaze-vpn/opt/phaze-vpn/phazebrowser/start-chromium-fetch.sh",
]

# Directories that might contain Chromium source (on VPS, not local)
# We'll create a script to clean VPS separately

print("="*80)
print("🗑️  REMOVING CHROMIUM-RELATED FILES")
print("="*80)
print("")
print("We're using WebKit, not Chromium - cleaning up Chromium files...")
print("")

deleted_count = 0
not_found_count = 0

for file_path in CHROMIUM_FILES:
    full_path = BASE_DIR / file_path
    if full_path.exists():
        try:
            if full_path.is_file():
                full_path.unlink()
                print(f"   ✅ Deleted: {file_path}")
                deleted_count += 1
            elif full_path.is_dir():
                shutil.rmtree(full_path)
                print(f"   ✅ Deleted directory: {file_path}")
                deleted_count += 1
        except Exception as e:
            print(f"   ⚠️  Error deleting {file_path}: {e}")
    else:
        not_found_count += 1

print("")
print("="*80)
print(f"✅ CLEANUP COMPLETE")
print("="*80)
print(f"   Deleted: {deleted_count} files")
print(f"   Not found: {not_found_count} files (already gone)")
print("")
print("📝 Next: Update documentation to remove Chromium references")
print("📝 Next: Clean up Chromium source on VPS (39GB)")

