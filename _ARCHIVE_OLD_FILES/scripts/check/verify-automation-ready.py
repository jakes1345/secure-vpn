#!/usr/bin/env python3
"""
Verify automation system is ready and will work
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file(filepath, description):
    """Check if file exists and is readable"""
    path = Path(filepath)
    if path.exists() and path.is_file():
        size = path.stat().st_size
        print(f"✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} - MISSING")
        return False

def check_process(process_name):
    """Check if process is running"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', process_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ {process_name}: Running (PIDs: {', '.join(pids)})")
            return True
        else:
            print(f"❌ {process_name}: Not running")
            return False
    except:
        print(f"⚠️  {process_name}: Could not check")
        return False

def main():
    print("=" * 70)
    print("🔍 VERIFYING AUTOMATION SYSTEM")
    print("=" * 70)
    print("")
    
    base_path = Path("/opt/phaze-vpn")
    all_good = True
    
    # Check scripts
    print("1️⃣ CHECKING SCRIPTS")
    print("-" * 70)
    
    scripts = [
        ("automated-browser-build.py", "Automated build script"),
        ("run-after-20min.sh", "Timer script"),
        ("check-browser-status-now.py", "Status check script"),
    ]
    
    for filepath, desc in scripts:
        if not check_file(base_path / filepath, desc):
            all_good = False
    
    print("")
    
    # Check if process is running
    print("2️⃣ CHECKING RUNNING PROCESSES")
    print("-" * 70)
    
    if not check_process("run-after-20min"):
        print("   ⚠️  Automation not running - will start it")
        all_good = False
    
    print("")
    
    # Check dependencies
    print("3️⃣ CHECKING DEPENDENCIES")
    print("-" * 70)
    
    try:
        import paramiko
        print("✅ paramiko: Available")
    except ImportError:
        print("❌ paramiko: NOT INSTALLED")
        print("   Install with: pip install paramiko")
        all_good = False
    
    print("")
    
    # Check VPS connectivity
    print("4️⃣ CHECKING VPS CONNECTIVITY")
    print("-" * 70)
    
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('15.204.11.19', username='root', password='Jakes1328!@', timeout=10)
        print("✅ VPS connection: WORKING")
        
        # Check key directories
        stdin, stdout, stderr = ssh.exec_command('test -d /opt/phazebrowser && echo YES || echo NO', timeout=5)
        if 'YES' in stdout.read().decode():
            print("✅ Browser directory: EXISTS")
        else:
            print("❌ Browser directory: MISSING")
            all_good = False
        
        stdin, stdout, stderr = ssh.exec_command('test -d /opt/depot_tools && echo YES || echo NO', timeout=5)
        if 'YES' in stdout.read().decode():
            print("✅ depot_tools: EXISTS")
        else:
            print("❌ depot_tools: MISSING")
            all_good = False
        
        ssh.close()
    except Exception as e:
        print(f"❌ VPS connection: FAILED - {e}")
        all_good = False
    
    print("")
    
    # Summary
    print("=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print("")
    
    if all_good:
        print("✅ ALL CHECKS PASSED!")
        print("")
        print("The automation system should work correctly.")
        print("")
        print("What will happen:")
        print("  1. Script waits 20 minutes")
        print("  2. Checks sync status on VPS")
        print("  3. Applies all modifications")
        print("  4. Generates build files")
        print("  5. Starts browser build")
        print("")
        print("Check status with: python3 check-browser-status-now.py")
    else:
        print("⚠️  SOME ISSUES FOUND")
        print("")
        print("Please fix the issues above before relying on automation.")
        print("")
        print("You can still run manually:")
        print("  python3 automated-browser-build.py")
    
    print("")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())

