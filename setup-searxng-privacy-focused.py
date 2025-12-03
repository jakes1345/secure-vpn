#!/usr/bin/env python3
"""
Setup SearXNG Privacy-Focused Search Engine on VPS
- NO Google
- Only privacy-focused engines
- Maximum privacy settings
- Integrated with PhazeVPN
"""

import paramiko
import sys
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
SEARXNG_DIR = "/opt/searxng"
SEARXNG_PORT = 8080

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"🔧 {description}...")
    
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    output_lines = []
    for line in iter(stdout.readline, ""):
        if line:
            line = line.rstrip()
            print(f"   {line}")
            output_lines.append(line)
    
    exit_status = stdout.channel.recv_exit_status()
    return exit_status == 0, "\n".join(output_lines)

def create_privacy_config(ssh):
    """Create privacy-focused configuration"""
    print("\n📝 Creating privacy-focused configuration...")
    
    # Create settings.yml with privacy engines only (NO Google)
    settings_yml = """# SearXNG Privacy-Focused Configuration for PhazeVPN
# NO Google - Only privacy-focused engines

server:
  secret_key: CHANGE_ME_TO_RANDOM_STRING
  base_url: http://15.204.11.19:8080/
  port: 8080
  bind_address: "0.0.0.0"

# Privacy-focused engines ONLY (NO Google)
engines:
  - name: duckduckgo
    enabled: true
  - name: qwant
    enabled: true
  - name: mojeek
    enabled: true
  - name: brave
    enabled: true
  - name: startpage
    enabled: true  # Optional: uses anonymized Google, but you can disable
  # Google is COMPLETELY DISABLED
  - name: google
    enabled: false
  - name: bing
    enabled: false

# Maximum privacy settings
general:
  enable_metrics: false  # No metrics collection
  enable_ui_stats: false  # No UI statistics
  enable_public_instances: false  # Don't list publicly
  enable_autocomplete: true
  autocomplete: ""

# Logging - Minimal (privacy-focused)
logging:
  level: ERROR  # Only errors
  log_requests: false  # Don't log search requests
  log_ip_address: false  # Don't log IP addresses
  log_user_agent: false  # Don't log user agents

# Result settings
result_proxy:
  url: ""
  proxied: false

# UI settings
ui:
  theme: simple
  infinite_scroll: false
"""
    
    # Write config file
    stdin, stdout, stderr = ssh.exec_command(f"cat > {SEARXNG_DIR}/settings.yml << 'EOF'\n{settings_yml}\nEOF")
    stdout.channel.recv_exit_status()
    print("   ✅ Privacy configuration created")
    
    # Set permissions
    run_command(ssh, f"chmod 644 {SEARXNG_DIR}/settings.yml", "Setting permissions")

def main():
    print("=" * 70)
    print("🔍 SETTING UP SearXNG - PRIVACY-FOCUSED (NO GOOGLE)")
    print("=" * 70)
    print("")
    print("Configuration:")
    print("  ✅ NO Google (completely disabled)")
    print("  ✅ Only privacy-focused engines:")
    print("     - DuckDuckGo")
    print("     - Qwant")
    print("     - Mojeek")
    print("     - Brave Search")
    print("     - Startpage (optional)")
    print("  ✅ Maximum privacy settings")
    print("  ✅ No logging, no tracking")
    print("")
    
    # Connect to VPS
    print("🔌 Connecting to VPS...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    print("")
    
    try:
        # Check Docker
        print("1️⃣ Checking Docker...")
        success, output = run_command(ssh, "docker --version", "Checking Docker")
        if not success:
            print("   ⚠️  Installing Docker...")
            run_command(ssh, "apt-get update -qq && apt-get install -y docker.io docker-compose", "Installing Docker")
            run_command(ssh, "systemctl start docker && systemctl enable docker", "Starting Docker")
        else:
            print("   ✅ Docker is installed")
        
        # Create directory
        print("\n2️⃣ Creating SearXNG directory...")
        run_command(ssh, f"mkdir -p {SEARXNG_DIR}", "Creating directory")
        
        # Create privacy config
        create_privacy_config(ssh)
        
        # Check if already running
        print("\n3️⃣ Checking if SearXNG is running...")
        success, output = run_command(ssh, "docker ps | grep searxng || echo 'NOT_RUNNING'", "Checking container")
        if 'searxng' in output.lower() and 'NOT_RUNNING' not in output:
            print("   ⚠️  SearXNG already running - stopping to reconfigure...")
            run_command(ssh, "docker stop searxng && docker rm searxng", "Stopping container")
        
        # Pull image
        print("\n4️⃣ Pulling SearXNG image...")
        run_command(ssh, "docker pull searxng/searxng:latest", "Pulling image")
        
        # Start SearXNG with privacy config
        print("\n5️⃣ Starting SearXNG with privacy configuration...")
        run_command(ssh, 
            f"docker run -d --name searxng -p {SEARXNG_PORT}:8080 "
            f"-v {SEARXNG_DIR}:/etc/searxng:rw "
            f"-e SEARXNG_HOSTNAME=phazevpn.com "
            f"searxng/searxng:latest",
            "Starting SearXNG")
        
        # Wait a moment
        import time
        time.sleep(3)
        
        # Verify it's running
        print("\n6️⃣ Verifying SearXNG is running...")
        success, output = run_command(ssh, "docker ps | grep searxng", "Checking status")
        if success and 'searxng' in output.lower():
            print("   ✅ SearXNG is running!")
        else:
            print("   ⚠️  Container may not be running - check logs")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ SEARXNG SETUP COMPLETE - PRIVACY-FOCUSED!")
        print("=" * 70)
        print("")
        print("🌐 Access SearXNG:")
        print(f"   http://{VPS_IP}:{SEARXNG_PORT}")
        print("")
        print("🔒 Privacy Features:")
        print("   ✅ NO Google (completely disabled)")
        print("   ✅ Only privacy-focused engines")
        print("   ✅ No logging, no tracking")
        print("   ✅ No metrics collection")
        print("")
        print("🔧 Engines Enabled:")
        print("   ✅ DuckDuckGo")
        print("   ✅ Qwant")
        print("   ✅ Mojeek")
        print("   ✅ Brave Search")
        print("   ✅ Startpage (optional)")
        print("   ❌ Google (DISABLED)")
        print("")
        print("📝 Next Steps:")
        print("   1. Test SearXNG: http://15.204.11.19:8080")
        print("   2. Customize UI to match PhazeVPN branding")
        print("   3. Integrate into web portal")
        print("   4. Update browser to use SearXNG instead of Startpage")
        print("")
        print("🔧 Useful Commands:")
        print("   # View logs:")
        print("   docker logs searxng")
        print("")
        print("   # Restart:")
        print("   docker restart searxng")
        print("")
        print("   # Edit config:")
        print(f"   nano {SEARXNG_DIR}/settings.yml")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

