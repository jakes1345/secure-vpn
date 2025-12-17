#!/usr/bin/env python3
"""
Review audit results on VPS using paramiko
"""

import paramiko
import sys
import os
from pathlib import Path

# VPS connection details
# Try IP first (more reliable), then domain
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"

def connect_vps():
    """Connect to VPS - tries SSH key first, then password"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Try SSH keys first
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                # Try RSA key
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                print(f"✅ Connected using SSH key: {key_path.name}")
                return ssh
            except:
                try:
                    # Try Ed25519 key
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    print(f"✅ Connected using SSH key: {key_path.name}")
                    return ssh
                except:
                    continue
    
    # Try without key (ssh-agent)
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        print("✅ Connected using SSH key from agent")
        return ssh
    except paramiko.AuthenticationException:
        pass
    
    # Fallback to password
    if VPS_PASSWORD:
        try:
            ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
            print("✅ Connected using password from environment")
            return ssh
        except paramiko.AuthenticationException:
            print(f"❌ Password authentication failed")
            print(f"   Check VPS_PASS or VPS_PASSWORD environment variable")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)
    else:
        print("❌ Authentication failed - no SSH key or password")
        print("   Options:")
        print("   1. Set up SSH key: ssh-copy-id root@15.204.11.19")
        print("   2. Or set password: export VPS_PASS='your_password'")
        sys.exit(1)

def get_audit_results(ssh):
    """Get audit results from VPS"""
    # Find latest audit directory
    stdin, stdout, stderr = ssh.exec_command(f"cd {VPS_DIR} && ls -td audit-results-* 2>/dev/null | head -1")
    audit_dir = stdout.read().decode().strip()
    if not audit_dir:
        # Try alternative path
        stdin, stdout, stderr = ssh.exec_command(f"cd /opt/phaze-vpn && ls -td audit-results-* 2>/dev/null | head -1")
        audit_dir = stdout.read().decode().strip()
    
    if not audit_dir:
        print("❌ No audit results found")
        return None
    
    print(f"📊 Found audit directory: {audit_dir}")
    
    # List audit files
    stdin, stdout, stderr = ssh.exec_command(f"cd {VPS_DIR} && ls -lh {audit_dir}/*.txt 2>/dev/null")
    files = stdout.read().decode()
    print("\n📁 Audit files:")
    print(files)
    
    return audit_dir

def review_critical_issues(ssh, audit_dir):
    """Review critical security issues"""
    print("\n🔒 Reviewing Critical Security Issues:")
    print("=" * 50)
    
    base_path = VPS_DIR if audit_dir.startswith('/') else f"{VPS_DIR}/{audit_dir}"
    
    # Dangerous functions
    print("\n1. Dangerous Functions (eval/exec):")
    stdin, stdout, stderr = ssh.exec_command(f"cat {base_path}/dangerous-functions.txt 2>/dev/null | head -30")
    dangerous = stdout.read().decode()
    if dangerous.strip():
        print(dangerous)
    else:
        print("  ✅ No dangerous functions found")
    
    # Hardcoded secrets
    print("\n2. Potential Hardcoded Secrets (first 20 lines):")
    stdin, stdout, stderr = ssh.exec_command(f"head -20 {base_path}/hardcoded-secrets.txt 2>/dev/null")
    secrets = stdout.read().decode()
    if secrets.strip():
        print(secrets)
        print("  ⚠️  Review and move secrets to environment variables")
    else:
        print("  ✅ No obvious hardcoded secrets found")
    
    # SQL queries (potential injection)
    print("\n3. SQL Queries (potential injection risks - first 10):")
    stdin, stdout, stderr = ssh.exec_command(f"head -10 {base_path}/sql-queries.txt 2>/dev/null")
    sql = stdout.read().decode()
    if sql.strip():
        print(sql)
        print("  ⚠️  Review all SQL queries for injection risks")
    else:
        print("  ✅ No SQL queries found")

def review_marketing_claims(ssh, audit_dir):
    """Review remaining marketing claims"""
    print("\n📢 Reviewing Marketing Claims:")
    print("=" * 50)
    
    base_path = VPS_DIR if audit_dir.startswith('/') else f"{VPS_DIR}/{audit_dir}"
    
    # Patent claims
    print("\n1. Patent Claims (first 10):")
    stdin, stdout, stderr = ssh.exec_command(f"head -10 {base_path}/patent-claims.txt 2>/dev/null")
    patents = stdout.read().decode()
    if patents.strip():
        print(patents)
        print("  ⚠️  Still has patent claims - need to remove")
    else:
        print("  ✅ No patent claims found")
    
    # Proprietary claims
    print("\n2. Proprietary Claims (first 10):")
    stdin, stdout, stderr = ssh.exec_command(f"head -10 {base_path}/proprietary-claims.txt 2>/dev/null")
    proprietary = stdout.read().decode()
    if proprietary.strip():
        print(proprietary)
        print("  ⚠️  Still has proprietary claims - need to remove")
    else:
        print("  ✅ No proprietary claims found")
    
    # Military-grade claims
    print("\n3. Military-Grade Claims (first 10):")
    stdin, stdout, stderr = ssh.exec_command(f"head -10 {base_path}/military-claims.txt 2>/dev/null")
    military = stdout.read().decode()
    if military.strip():
        print(military)
        print("  ⚠️  Still has military-grade claims - need to update")
    else:
        print("  ✅ No military-grade claims found")

def main():
    print("🔍 Connecting to VPS to review audit results...")
    print("")
    
    ssh = connect_vps()
    
    try:
        # Get audit results
        audit_dir = get_audit_results(ssh)
        if not audit_dir:
            return
        
        # Review critical issues
        review_critical_issues(ssh, audit_dir)
        
        # Review marketing claims
        review_marketing_claims(ssh, audit_dir)
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 SUMMARY:")
        print("  - Review dangerous-functions.txt for security risks")
        print("  - Review sql-queries.txt for injection risks")
        print("  - Fix remaining marketing claims")
        print("  - Consider replacing print() with logging")
        if audit_dir.startswith('/'):
            print(f"\n  Full audit results: {audit_dir}/")
        else:
            print(f"\n  Full audit results: {VPS_DIR}/{audit_dir}/")
        
    finally:
        ssh.close()
        print("\n✅ Disconnected from VPS")

if __name__ == '__main__':
    main()

