#!/usr/bin/env python3
"""
Comprehensive diagnosis of ALL potential sync issues
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/phazebrowser"

def check_issue(ssh, check_name, command, expected_result=None):
    """Check a specific issue"""
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
        result = stdout.read().decode().strip()
        errors = stderr.read().decode().strip()
        
        if expected_result:
            passed = expected_result in result or expected_result in errors
        else:
            passed = result and "error" not in result.lower() and "failed" not in result.lower()
        
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed or errors:
            print(f"   Result: {result[:100] if result else 'No output'}")
            if errors:
                print(f"   Errors: {errors[:100]}")
        return passed
    except Exception as e:
        print(f"⚠️  {check_name}: Error - {e}")
        return False

def main():
    print("=" * 70)
    print("🔍 COMPREHENSIVE SYNC DIAGNOSIS")
    print("=" * 70)
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    issues_found = []
    
    try:
        # 1. Network Connectivity
        print("1️⃣ NETWORK & CONNECTIVITY")
        print("-" * 70)
        if not check_issue(ssh, "Internet connectivity", "ping -c 1 8.8.8.8 2>&1 | grep '1 received'", "1 received"):
            issues_found.append("No internet connectivity")
        if not check_issue(ssh, "DNS resolution", "nslookup chromium.googlesource.com 2>&1 | grep -i 'name:'", "name"):
            issues_found.append("DNS resolution issues")
        if not check_issue(ssh, "Git access", "git ls-remote https://chromium.googlesource.com/chromium/src.git HEAD 2>&1 | head -1", "refs/heads"):
            issues_found.append("Cannot access Chromium git repository")
        print("")
        
        # 2. Disk Space
        print("2️⃣ DISK SPACE")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1 | awk '{print $4, $5}'")
        disk_info = stdout.read().decode().strip()
        print(f"✅ Main disk: {disk_info}")
        stdin, stdout, stderr = ssh.exec_command("df -h /mnt/extra-disk | tail -1 | awk '{print $4, $5}'")
        extra_disk = stdout.read().decode().strip()
        print(f"✅ Extra disk: {extra_disk}")
        
        # Check if we have enough space (need at least 5GB)
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1 | awk '{print $4}' | sed 's/G//'")
        try:
            free_gb = float(stdout.read().decode().strip().replace('G', '').replace('M', '0'))
            if free_gb < 5:
                issues_found.append(f"Low disk space on main disk: {free_gb}GB")
                print(f"❌ Low disk space: {free_gb}GB (need 5GB+)")
            else:
                print(f"✅ Sufficient space: {free_gb}GB")
        except:
            pass
        print("")
        
        # 3. Filesystem Issues
        print("3️⃣ FILESYSTEM & CROSS-DEVICE")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("readlink -f /opt/phazebrowser/.cipd")
        cache_path = stdout.read().decode().strip()
        stdin, stdout, stderr = ssh.exec_command("readlink -f /opt/phazebrowser/src")
        src_path = stdout.read().decode().strip()
        
        # Check if on same filesystem
        stdin, stdout, stderr = ssh.exec_command(f"df {cache_path} 2>/dev/null | tail -1 | awk '{{print $1}}'")
        cache_fs = stdout.read().decode().strip()
        stdin, stdout, stderr = ssh.exec_command(f"df {src_path} 2>/dev/null | tail -1 | awk '{{print $1}}'")
        src_fs = stdout.read().decode().strip()
        
        if cache_fs == src_fs and cache_fs:
            print(f"✅ Cache and source on same filesystem: {cache_fs}")
        else:
            issues_found.append("Cache and source on different filesystems")
            print(f"❌ Different filesystems!")
            print(f"   Cache: {cache_fs}")
            print(f"   Source: {src_fs}")
        print("")
        
        # 4. Permissions
        print("4️⃣ PERMISSIONS")
        print("-" * 70)
        if not check_issue(ssh, "Write permission to source", f"test -w {VPS_PATH}/src && echo YES || echo NO", "YES"):
            issues_found.append("No write permission to source directory")
        if not check_issue(ssh, "Write permission to cache", f"test -w /opt/phazebrowser/.cipd && echo YES || echo NO", "YES"):
            issues_found.append("No write permission to cache directory")
        print("")
        
        # 5. Dependencies
        print("5️⃣ DEPENDENCIES")
        print("-" * 70)
        if not check_issue(ssh, "depot_tools installed", "test -d /opt/depot_tools && echo YES || echo NO", "YES"):
            issues_found.append("depot_tools not installed")
        if not check_issue(ssh, "git installed", "which git", "/usr/bin/git"):
            issues_found.append("git not installed")
        if not check_issue(ssh, "python3 available", "which python3", "/usr/bin/python3"):
            issues_found.append("python3 not available")
        if not check_issue(ssh, "curl available", "which curl", "/usr/bin/curl"):
            issues_found.append("curl not installed")
        print("")
        
        # 6. Configuration
        print("6️⃣ CONFIGURATION")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command(f"test -f {VPS_PATH}/.gclient && echo YES || echo NO")
        has_gclient = stdout.read().decode().strip() == 'YES'
        print(f"{'✅' if has_gclient else '❌'} .gclient file: {'EXISTS' if has_gclient else 'MISSING'}")
        
        if has_gclient:
            stdin, stdout, stderr = ssh.exec_command(f"cat {VPS_PATH}/.gclient")
            gclient_content = stdout.read().decode()
            if 'chromium.googlesource.com' in gclient_content:
                print("✅ .gclient config looks valid")
            else:
                issues_found.append(".gclient configuration invalid")
                print("❌ .gclient config may be invalid")
        print("")
        
        # 7. Git Repository State
        print("7️⃣ GIT REPOSITORY STATE")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command(f"cd {VPS_PATH}/src && git status 2>&1 | head -5")
        git_status = stdout.read().decode()
        if "not a git repository" in git_status.lower():
            issues_found.append("Source is not a git repository")
            print("❌ Not a git repository")
        elif "fatal" in git_status.lower():
            issues_found.append("Git repository corrupted")
            print(f"❌ Git error: {git_status[:100]}")
        else:
            print("✅ Git repository looks OK")
        print("")
        
        # 8. Environment Variables
        print("8️⃣ ENVIRONMENT VARIABLES")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("echo $CIPD_CACHE_DIR")
        cipd_cache = stdout.read().decode().strip()
        if cipd_cache:
            print(f"✅ CIPD_CACHE_DIR: {cipd_cache}")
        else:
            print("⚠️  CIPD_CACHE_DIR not set (may be OK)")
        
        stdin, stdout, stderr = ssh.exec_command("echo $PATH | grep depot_tools")
        depot_in_path = stdout.read().decode().strip()
        if depot_in_path:
            print("✅ depot_tools in PATH")
        else:
            issues_found.append("depot_tools not in PATH")
            print("❌ depot_tools not in PATH")
        print("")
        
        # 9. Running Processes
        print("9️⃣ RUNNING PROCESSES")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep '[g]client sync' | wc -l")
        sync_count = int(stdout.read().decode().strip())
        if sync_count > 0:
            print(f"✅ Sync process running ({sync_count} process(es))")
        else:
            print("❌ No sync process running")
            issues_found.append("Sync process not running")
        print("")
        
        # 10. Recent Errors
        print("🔟 RECENT ERRORS IN LOG")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("tail -50 /tmp/chromium-sync-fixed.log 2>/dev/null | grep -iE 'error|failed|fatal' | tail -5")
        errors = stdout.read().decode()
        if errors.strip():
            print("⚠️  Recent errors found:")
            for line in errors.strip().split('\n')[:5]:
                if line.strip():
                    print(f"   {line[:80]}")
                    # Check for specific known issues
                    if 'cross-device' in line.lower() or 'invalid cross-device' in line.lower():
                        issues_found.append("Cross-device link errors still occurring")
                    if 'no space' in line.lower() or 'disk full' in line.lower():
                        issues_found.append("Disk space errors")
                    if 'permission denied' in line.lower():
                        issues_found.append("Permission errors")
        else:
            print("✅ No recent errors in log")
        print("")
        
        # Summary
        print("=" * 70)
        print("📋 DIAGNOSIS SUMMARY")
        print("=" * 70)
        print("")
        
        if issues_found:
            print(f"❌ Found {len(issues_found)} potential issue(s):")
            for i, issue in enumerate(issues_found, 1):
                print(f"   {i}. {issue}")
            print("")
            print("🔧 These need to be fixed for sync to work properly")
        else:
            print("✅ No major issues found!")
            print("   Sync should work, but may take time")
        
        print("")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

