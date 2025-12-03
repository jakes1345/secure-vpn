#!/usr/bin/env python3
"""
Comprehensive verification of everything - browser, design files, VPS status
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if file exists"""
    path = Path(filepath)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath} ({size} bytes)")
    return exists

def main():
    print("=" * 70)
    print("🔍 COMPREHENSIVE VERIFICATION CHECK")
    print("=" * 70)
    print("")
    
    base_path = Path("/opt/phaze-vpn")
    all_good = True
    
    # 1. Design Documentation Files
    print("=" * 70)
    print("1️⃣ DESIGN DOCUMENTATION FILES")
    print("=" * 70)
    print("")
    
    design_files = [
        ("phazebrowser/DESIGN-SPECIFICATION.md", "Design Specification"),
        ("phazebrowser/DESIGN-OPERA-GX-INSPIRED.md", "Opera GX Inspired Design"),
        ("phazebrowser/DESIGN-DISCUSSION.md", "Design Discussion"),
        ("phazebrowser/VISUAL-MOCKUPS.md", "Visual Mockups"),
        ("phazebrowser/ANIMATION-SPECIFICATIONS.md", "Animation Specifications"),
        ("phazebrowser/STYLE-GUIDE.md", "Style Guide"),
    ]
    
    for filepath, desc in design_files:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 2. CSS/Design System Files
    print("=" * 70)
    print("2️⃣ CSS & DESIGN SYSTEM FILES")
    print("=" * 70)
    print("")
    
    css_files = [
        ("phazebrowser/styles/design-system.css", "Design System CSS"),
    ]
    
    for filepath, desc in css_files:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 3. Component Files
    print("=" * 70)
    print("3️⃣ COMPONENT FILES")
    print("=" * 70)
    print("")
    
    component_files = [
        ("phazebrowser/components/README.md", "Components README"),
        ("phazebrowser/components/Sidebar.jsx", "Sidebar Component"),
        ("phazebrowser/components/Sidebar.css", "Sidebar Styles"),
        ("phazebrowser/components/VPNStatusPanel.jsx", "VPN Status Panel"),
        ("phazebrowser/components/VPNStatusPanel.css", "VPN Panel Styles"),
    ]
    
    for filepath, desc in component_files:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 4. Icon Design Files
    print("=" * 70)
    print("4️⃣ ICON DESIGN FILES")
    print("=" * 70)
    print("")
    
    icon_files = [
        ("phazebrowser/icons/ICON-DESIGN.md", "Icon Design Guide"),
    ]
    
    for filepath, desc in icon_files:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 5. Browser Source Code Files
    print("=" * 70)
    print("5️⃣ BROWSER SOURCE CODE FILES")
    print("=" * 70)
    print("")
    
    source_files = [
        ("phazebrowser/src/vpn_manager.cc", "VPN Manager Source"),
        ("phazebrowser/src/webrtc_vpn_patch.cc", "WebRTC VPN Patch"),
        ("phazebrowser/src/ipv6_vpn_patch.cc", "IPv6 VPN Patch"),
        ("phazebrowser/patches/vpn-integration.patch", "VPN Integration Patch"),
        ("phazebrowser/patches/webrtc-vpn-routing.patch", "WebRTC Routing Patch"),
    ]
    
    for filepath, desc in source_files:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 6. Build & Setup Scripts
    print("=" * 70)
    print("6️⃣ BUILD & SETUP SCRIPTS")
    print("=" * 70)
    print("")
    
    script_files = [
        ("phazebrowser/build.sh", "Build Script"),
        ("phazebrowser/setup-on-vps.sh", "VPS Setup Script"),
        ("phazebrowser/apply-modifications.sh", "Apply Modifications Script"),
    ]
    
    for filepath, desc in script_files:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 7. Documentation Files
    print("=" * 70)
    print("7️⃣ DOCUMENTATION FILES")
    print("=" * 70)
    print("")
    
    doc_files = [
        ("phazebrowser/README.md", "Browser README"),
        ("phazebrowser/BUILD-INSTRUCTIONS.md", "Build Instructions"),
        ("phazebrowser/DEVELOPMENT-ROADMAP.md", "Development Roadmap"),
        ("phazebrowser/BROWSER-TODO.md", "Browser TODO"),
    ]
    
    for filepath, desc in doc_files:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 8. VPS Status Scripts
    print("=" * 70)
    print("8️⃣ VPS STATUS & FIX SCRIPTS")
    print("=" * 70)
    print("")
    
    vps_scripts = [
        ("check-browser-status-vps.py", "Browser Status Check"),
        ("check-browser-status-now.py", "Quick Status Check"),
        ("fix-browser-vps-complete.py", "Complete Browser Fix"),
        ("fix-and-start-browser-vps.py", "Fix and Start Build"),
        ("sync-and-build-browser-vps.py", "Sync and Build"),
        ("force-complete-sync-vps.py", "Force Complete Sync"),
        ("fix-sync-directory-issue.py", "Fix Sync Directory"),
    ]
    
    for filepath, desc in vps_scripts:
        if not check_file_exists(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # 9. Check VPS Status
    print("=" * 70)
    print("9️⃣ VPS STATUS (Remote Check)")
    print("=" * 70)
    print("")
    
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('15.204.11.19', username='root', password='Jakes1328!@', timeout=10)
        
        # Check disk space
        stdin, stdout, stderr = ssh.exec_command('df -h / | tail -1')
        disk = stdout.read().decode().strip()
        print(f"✅ Disk space: {disk}")
        
        # Check if Chromium source exists
        stdin, stdout, stderr = ssh.exec_command('test -d /opt/phazebrowser/src && du -sh /opt/phazebrowser/src 2>/dev/null | head -1 || echo MISSING')
        src_size = stdout.read().decode().strip()
        print(f"✅ Chromium source: {src_size}")
        
        # Check if sync is running
        stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[g]client sync" | wc -l')
        sync_running = int(stdout.read().decode().strip()) > 0
        print(f"{'✅' if sync_running else '❌'} Sync running: {sync_running}")
        
        # Check if GN tool exists
        stdin, stdout, stderr = ssh.exec_command('test -f /opt/phazebrowser/src/buildtools/linux64/gn/gn && echo YES || echo NO')
        gn_exists = stdout.read().decode().strip()
        print(f"{'✅' if gn_exists == 'YES' else '❌'} GN tool: {gn_exists}")
        
        # Check if build directory exists
        stdin, stdout, stderr = ssh.exec_command('test -d /opt/phazebrowser/src/build/config && echo YES || echo NO')
        build_config = stdout.read().decode().strip()
        print(f"{'✅' if build_config == 'YES' else '❌'} Build config dir: {build_config}")
        
        ssh.close()
    except ImportError:
        print("⚠️  paramiko not available - skipping VPS check")
    except Exception as e:
        print(f"⚠️  VPS check failed: {e}")
    
    print("")
    
    # 10. Summary
    print("=" * 70)
    print("🔟 SUMMARY")
    print("=" * 70)
    print("")
    
    if all_good:
        print("✅ All local files verified!")
    else:
        print("❌ Some files are missing!")
        print("   Check the list above for missing files")
    
    print("")
    print("📋 Next Steps:")
    print("   1. Wait for sync to complete (10-30 minutes)")
    print("   2. Check status: python3 check-browser-status-now.py")
    print("   3. Once sync done, run: python3 fix-and-start-browser-vps.py")
    print("")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())

