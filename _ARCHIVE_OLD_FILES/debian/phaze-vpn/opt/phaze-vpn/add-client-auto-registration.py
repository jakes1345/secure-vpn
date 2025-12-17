#!/usr/bin/env python3
"""
Add auto-registration to client GUI
Clients register with VPS on first run
"""

import re
import uuid
import platform
import subprocess

# Read vpn-gui.py
gui_file = '/opt/phaze-vpn/vpn-gui.py'
with open(gui_file, 'r') as f:
    content = f.read()

# Check if registration already exists
if 'def register_with_vps' in content:
    print("✅ Client registration already exists")
    exit(0)

# Get MAC address function
get_mac_code = '''
def get_client_id():
    """Get unique client identifier (MAC address)"""
    try:
        import uuid
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0,2*6,2)][::-1])
        return mac
    except:
        # Fallback to UUID
        return str(uuid.uuid4())
'''

# Registration function
registration_code = '''
    def register_with_vps(self):
        """Register this client with the VPS on first run"""
        try:
            # Get client ID from config or generate
            config_file = VPN_DIR / 'client_id.txt'
            if config_file.exists():
                client_id = config_file.read_text().strip()
            else:
                # Generate unique client ID (MAC address)
                import uuid
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
                client_id = mac
                # Save it
                config_file.write_text(client_id)
            
            # Get system info
            hostname = platform.node()
            os_type = platform.system()
            os_version = platform.release()
            client_version = "1.0.1"  # Current version
            
            # Register with VPS
            register_url = f"{self.api_base_url}/api/v1/client/register"
            register_data = {
                'client_id': client_id,
                'hostname': hostname,
                'os': os_type,
                'os_version': os_version,
                'version': client_version,
                'username': self.username if hasattr(self, 'username') else '',
                'password': self.password if hasattr(self, 'password') else ''
            }
            
            response = requests.post(
                register_url,
                json=register_data,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                self.client_id = client_id
                self.subscription = data.get('subscription', {})
                self.vpn_config_name = data.get('vpn_config_url', '').split('/')[-1] if data.get('vpn_config_url') else None
                
                # Download VPN config if available
                if self.vpn_config_name:
                    self.download_vpn_config()
                
                return True
            else:
                print(f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def download_vpn_config(self):
        """Download VPN config from VPS"""
        try:
            if not self.vpn_config_name:
                return
            
            download_url = f"{self.api_base_url}/download/{self.vpn_config_name}"
            response = requests.get(download_url, timeout=10, verify=False)
            
            if response.status_code == 200:
                config_dir = VPN_DIR / 'client-configs'
                config_dir.mkdir(exist_ok=True)
                config_file = config_dir / f'{self.vpn_config_name}.ovpn'
                config_file.write_text(response.text)
                print(f"VPN config downloaded: {config_file}")
        except Exception as e:
            print(f"Failed to download config: {e}")
    
    def client_checkin(self):
        """Periodic check-in with VPS"""
        try:
            if not hasattr(self, 'client_id'):
                return
            
            checkin_url = f"{self.api_base_url}/api/v1/client/checkin"
            response = requests.post(
                checkin_url,
                json={'client_id': self.client_id},
                timeout=5,
                verify=False
            )
        except:
            pass  # Silent fail for check-in
'''

# Find where to insert (in VPNDashboard __init__)
if 'class VPNDashboard:' in content:
    # Find the end of __init__ method
    init_match = re.search(r'def __init__\(self[^:]*:.*?(?=    def |class |$)', content, re.DOTALL)
    if init_match:
        init_end = init_match.end()
        # Insert registration call at end of __init__
        insert_code = '''
        
        # Register with VPS on first run
        self.client_id = None
        self.subscription = {}
        self.vpn_config_name = None
        self.register_with_vps()
        
        # Setup periodic check-in (every 5 minutes)
        self.root.after(300000, self.client_checkin)  # 5 minutes
'''
        new_content = content[:init_end] + insert_code + content[init_end:]
    else:
        # Insert before class methods
        class_pos = content.find('class VPNDashboard:')
        methods_pos = content.find('    def ', class_pos + 100)
        new_content = content[:methods_pos] + registration_code + '\n' + content[methods_pos:]
else:
    new_content = content + registration_code

# Write back
with open(gui_file, 'w') as f:
    f.write(new_content)

print("✅ Added client auto-registration")

