#!/usr/bin/env python3
"""
Pre and Post Deployment Verification
Tests everything via SSH (paramiko) - runs from your PC
"""

import os
import sys
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy
import json
from datetime import datetime

# VPS Configuration - ALWAYS use SSH/paramiko
VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASS = os.environ.get('VPS_PASS', 'Jakes1328!@')
VPN_DIR_ON_VPS = "/opt/secure-vpn"

class DeploymentVerifier:
    def __init__(self):
        self.ssh = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
    
    def connect(self):
        """Connect to VPS via SSH (paramiko)"""
        try:
            print("📡 Connecting to VPS via SSH...")
            self.ssh = SSHClient()
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())
            self.ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
            print("   ✅ Connected!")
            return True
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
    
    def check(self, name, check_func, critical=True):
        """Run a check"""
        try:
            result = check_func()
            if result:
                print(f"   ✅ {name}")
                self.results['checks'][name] = {'status': 'passed', 'critical': critical}
                self.results['passed'] += 1
                return True
            else:
                status = 'failed' if critical else 'warning'
                print(f"   {'❌' if critical else '⚠️'} {name}")
                self.results['checks'][name] = {'status': status, 'critical': critical}
                if critical:
                    self.results['failed'] += 1
                else:
                    self.results['warnings'] += 1
                return False
        except Exception as e:
            print(f"   ❌ {name} - Error: {e}")
            self.results['checks'][name] = {'status': 'error', 'error': str(e), 'critical': critical}
            if critical:
                self.results['failed'] += 1
            return False
    
    def verify_files(self):
        """Verify all critical files exist"""
        print("\n📁 Verifying Files...")
        
        critical_files = [
            f"{VPN_DIR_ON_VPS}/config/server.conf",
            f"{VPN_DIR_ON_VPS}/vpn-manager.py",
            f"{VPN_DIR_ON_VPS}/vpn-gui.py",
            f"{VPN_DIR_ON_VPS}/web-portal/app.py",
            f"{VPN_DIR_ON_VPS}/multi-ip-manager.py",
            f"{VPN_DIR_ON_VPS}/scripts/setup-wireguard.sh",
            f"{VPN_DIR_ON_VPS}/scripts/optimize-for-gaming.sh",
        ]
        
        all_exist = True
        for file_path in critical_files:
            stdin, stdout, stderr = self.exec_command(f"test -f '{file_path}' && echo 'exists' || echo 'missing'")
            exists = stdout.read().decode().strip() == 'exists'
            if not exists:
                print(f"   ❌ Missing: {file_path}")
                all_exist = False
            else:
                print(f"   ✅ {file_path}")
        
        return all_exist
    
    def verify_services(self):
        """Verify services are running"""
        print("\n🔄 Verifying Services...")

        # Check OpenVPN
        stdin, stdout, stderr = self.exec_command("systemctl is-active secure-vpn || pgrep -f 'openvpn.*server.conf' || echo 'not-running'")
        openvpn_running = 'active' in stdout.read().decode() or 'openvpn' in stdout.read().decode()
        
        # Check web portal
        stdin, stdout, stderr = self.exec_command("systemctl is-active phazevpn-web || pgrep -f 'app.py' || echo 'not-running'")
        web_running = 'active' in stdout.read().decode() or 'app.py' in stdout.read().decode()
        
        return openvpn_running, web_running
    
    def verify_ports(self):
        """Verify ports are open"""
        print("\n🔌 Verifying Ports...")
        
        # Check port 1194 (OpenVPN)
        stdin, stdout, stderr = self.exec_command("netstat -uln | grep ':1194 ' || ss -uln | grep ':1194 ' || echo 'not-listening'")
        port_1194 = ':1194' in stdout.read().decode()
        
        # Check port 8081 (Download server)
        stdin, stdout, stderr = self.exec_command("netstat -tln | grep ':8081 ' || ss -tln | grep ':8081 ' || echo 'not-listening'")
        port_8081 = ':8081' in stdout.read().decode()
        
        return port_1194, port_8081
    
    def verify_python_packages(self):
        """Verify Python packages are installed"""
        print("\n📦 Verifying Python Packages...")
        
        stdin, stdout, stderr = self.exec_command(
            f"cd {VPN_DIR_ON_VPS}/web-portal && python3 -c 'import flask, paramiko' 2>&1"
        )
        result = stdout.read().decode()
        return 'Error' not in result and 'ModuleNotFoundError' not in result
    
    def verify_permissions(self):
        """Verify file permissions"""
        print("\n🔐 Verifying Permissions...")
        
        # Check scripts are executable
        scripts = [
            f"{VPN_DIR_ON_VPS}/scripts/setup-wireguard.sh",
            f"{VPN_DIR_ON_VPS}/scripts/optimize-for-gaming.sh",
            f"{VPN_DIR_ON_VPS}/multi-ip-manager.py",
]

        all_executable = True
        for script in scripts:
            stdin, stdout, stderr = self.exec_command(f"test -x '{script}' && echo 'executable' || echo 'not-executable'")
            is_executable = stdout.read().decode().strip() == 'executable'
            if not is_executable:
                print(f"   ⚠️  Not executable: {script}")
                all_executable = False
        
        return all_executable
    
    def run_all_checks(self):
        """Run all verification checks"""
        print("="*70)
        print("🔍 DEPLOYMENT VERIFICATION")
        print("="*70)
print("")

        if not self.connect():
            return False
        
        # File checks
        self.check("Critical files exist", self.verify_files, critical=True)
        
        # Service checks
        openvpn_running, web_running = self.verify_services()
        self.check("OpenVPN service", lambda: openvpn_running, critical=False)
        self.check("Web portal service", lambda: web_running, critical=False)
        
        # Port checks
        port_1194, port_8081 = self.verify_ports()
        self.check("Port 1194 (OpenVPN)", lambda: port_1194, critical=True)
        self.check("Port 8081 (Download)", lambda: port_8081, critical=False)
        
        # Package checks
        self.check("Python packages", self.verify_python_packages, critical=True)
        
        # Permission checks
        self.check("Script permissions", self.verify_permissions, critical=False)
        
        # Summary
        print("")
        print("="*70)
        print("📊 VERIFICATION SUMMARY")
        print("="*70)
        print(f"   ✅ Passed: {self.results['passed']}")
        print(f"   ❌ Failed: {self.results['failed']}")
        print(f"   ⚠️  Warnings: {self.results['warnings']}")
print("")

        if self.results['failed'] == 0:
            print("✅ All critical checks passed!")
            return True
else:
            print("❌ Some critical checks failed!")
            return False
    
    def save_results(self):
        """Save verification results"""
        results_file = Path(__file__).parent / 'verification-results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Results saved to: {results_file}")
    
    def close(self):
        """Close SSH connection"""
        if self.ssh:
            self.ssh.close()

def main():
    verifier = DeploymentVerifier()
    try:
        success = verifier.run_all_checks()
        verifier.save_results()
        return 0 if success else 1
    finally:
        verifier.close()

if __name__ == '__main__':
    sys.exit(main())
