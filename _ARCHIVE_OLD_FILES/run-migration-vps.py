#!/usr/bin/env python3
"""Run database migration on VPS"""

import paramiko
import os
import sys

VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASS = os.environ.get('VPS_PASS', '')
MYSQL_PASS = os.environ.get('MYSQL_PASSWORD', 'PhazeVPN2025SecureDB!')

if not VPS_PASS:
    print("❌ Error: VPS_PASS environment variable not set")
    print("   Set it with: export VPS_PASS='your-password'")
    sys.exit(1)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("=" * 80)
print("🔒 RUNNING PRIVACY MIGRATION")
print("=" * 80)
print()

# Read migration SQL
migration_file = "/opt/secure-vpn/web-portal/remove_ip_tracking_migration.sql"
print(f"Reading migration file: {migration_file}...")

stdin, stdout, stderr = ssh.exec_command(f"cat {migration_file}")
migration_sql = stdout.read().decode()
error = stderr.read().decode()

if not migration_sql:
    print(f"❌ Could not read migration file: {error}")
    ssh.close()
    exit(1)

print("✅ Migration file found")
print()

# Run migration
print("Running migration...")
print("(This removes IP tracking from database)")
print()

# Execute migration
stdin, stdout, stderr = ssh.exec_command(
    f"mysql -u phazevpn -p'{MYSQL_PASS}' phazevpn < {migration_file} 2>&1"
)

output = stdout.read().decode()
error = stderr.read().decode()

if error and 'ERROR' in error:
    print("❌ Migration errors:")
    print(error)
else:
    print("✅ Migration completed successfully!")
    if output:
        print(output)

# Verify changes
print("\nVerifying changes...")
stdin, stdout, stderr = ssh.exec_command(
    f"mysql -u phazevpn -p'{MYSQL_PASS}' phazevpn -e \"SHOW COLUMNS FROM connection_history LIKE 'ip_address'; SHOW COLUMNS FROM rate_limits LIKE 'ip_address'; SHOW COLUMNS FROM rate_limits LIKE 'username';\" 2>&1"
)
output = stdout.read().decode()
print(output)

ssh.close()
print("\n✅ Done")
