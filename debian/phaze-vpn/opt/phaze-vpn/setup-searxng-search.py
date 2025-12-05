#!/usr/bin/env python3
"""
Setup SearXNG Privacy-Focused Search Engine on VPS
Integrates with PhazeVPN portal
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

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

def main():
    print("=" * 70)
    print("🔍 SETTING UP SearXNG PRIVACY SEARCH ENGINE")
    print("=" * 70)
    print("")
    print("SearXNG is a privacy-focused meta search engine")
    print("Perfect for PhazeVPN - no tracking, no logging, fully customizable")
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
        # Check if Docker is installed
        print("1️⃣ Checking Docker installation...")
        success, output = run_command(ssh, "docker --version", "Checking Docker")
        if success:
            print("   ✅ Docker is installed")
        else:
            print("   ⚠️  Docker not found - installing...")
            run_command(ssh, "apt-get update -qq && apt-get install -y docker.io docker-compose", "Installing Docker")
            run_command(ssh, "systemctl start docker && systemctl enable docker", "Starting Docker")
        
        # Check if SearXNG is already running
        print("\n2️⃣ Checking if SearXNG is already running...")
        success, output = run_command(ssh, "docker ps | grep searxng || echo 'NOT_RUNNING'", "Checking SearXNG")
        if 'searxng' in output.lower() and 'NOT_RUNNING' not in output:
            print("   ✅ SearXNG is already running")
            print("   📝 To access: http://15.204.11.19:8080")
        else:
            print("   ⚠️  SearXNG not running - setting up...")
            
            # Create SearXNG directory
            print("\n3️⃣ Creating SearXNG directory...")
            run_command(ssh, "mkdir -p /opt/searxng", "Creating directory")
            
            # Pull SearXNG image
            print("\n4️⃣ Pulling SearXNG Docker image...")
            run_command(ssh, "docker pull searxng/searxng:latest", "Pulling image")
            
            # Run SearXNG
            print("\n5️⃣ Starting SearXNG...")
            run_command(ssh, 
                "docker run -d --name searxng -p 8080:8080 -v /opt/searxng:/etc/searxng:rw searxng/searxng:latest",
                "Starting SearXNG container")
            
            print("   ✅ SearXNG started!")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ SEARXNG SETUP COMPLETE!")
        print("=" * 70)
        print("")
        print("🌐 Access SearXNG:")
        print("   http://15.204.11.19:8080")
        print("")
        print("🔧 Next Steps:")
        print("   1. Access SearXNG and test it")
        print("   2. Customize the UI to match PhazeVPN branding")
        print("   3. Integrate into web portal")
        print("   4. Configure search engines")
        print("")
        print("📝 Useful Commands:")
        print("   # View logs:")
        print("   docker logs searxng")
        print("")
        print("   # Restart:")
        print("   docker restart searxng")
        print("")
        print("   # Stop:")
        print("   docker stop searxng")
        print("")
        print("   # Customize config:")
        print("   # Edit: /opt/searxng/settings.yml")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

