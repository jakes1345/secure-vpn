#!/usr/bin/env python3
"""
Improve update mechanism to fully reinstall client
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Read current vpn-gui.py
gui_file = Path('/opt/phaze-vpn/vpn-gui.py')
if not gui_file.exists():
    gui_file = Path('/opt/phaze-vpn/vpn-gui.py')

with open(gui_file, 'r') as f:
    content = f.read()

# Find the check_for_updates method
old_update_method = '''    def check_for_updates(self):
        """Check for client updates"""
        def do_check():
            try:
                # Get current version
                version_file = VPN_DIR / 'VERSION'
                if version_file.exists():
                    current_version = version_file.read_text().strip()
                else:
                    current_version = "1.0.0"
                
                # Check for updates via API
                update_url = f"{self.api_base_url}/api/v1/update/check"
                response = requests.get(
                    update_url,
                    params={'version': current_version},
                    timeout=10,
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    has_update = data.get('has_update', False)
                    latest_version = data.get('current_version', current_version)
                    download_url = data.get('download_url', '')
                    
                    if has_update:
                        msg = f"🔄 Update Available!\\n\\n"
                        msg += f"Current Version: {current_version}\\n"
                        msg += f"Latest Version: {latest_version}\\n\\n"
                        msg += f"Would you like to download the update?"
                        
                        if messagebox.askyesno("Update Available", msg):
                            import webbrowser
                            if download_url:
                                webbrowser.open(download_url)
                            else:
                                webbrowser.open(f"{self.api_base_url}/download/client/linux")
                    else:
                        messagebox.showinfo("No Updates", 
                                          f"You're running the latest version!\\n\\n"
                                          f"Current Version: {current_version}")
                else:
                    messagebox.showerror("Update Check Failed", 
                                       f"Failed to check for updates.\\n"
                                       f"HTTP {response.status_code}")
            except requests.exceptions.ConnectionError:
                messagebox.showerror("Connection Error", 
                                   "Failed to connect to update server.\\n"
                                   "Please check your internet connection.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to check for updates: {e}")
        
        # Show checking message
        checking_window = tk.Toplevel(self.root)
        checking_window.title("Checking for Updates")
        checking_window.geometry("300x100")
        checking_window.configure(bg='#2b2b2b')
        checking_window.transient(self.root)
        checking_window.grab_set()
        
        tk.Label(checking_window, text="Checking for updates...", 
                bg='#2b2b2b', fg='#ffffff',
                font=('Arial', 12)).pack(pady=30)
        
        # Run check in background
        def close_and_check():
            checking_window.destroy()
            do_check()
        
        checking_window.after(500, close_and_check)'''

new_update_method = '''    def check_for_updates(self):
        """Check for client updates and install automatically"""
        def do_check():
            try:
                # Get current version
                version_file = VPN_DIR / 'VERSION'
                if version_file.exists():
                    current_version = version_file.read_text().strip()
                else:
                    current_version = "1.0.0"
                
                # Check for updates via API
                update_url = f"{self.api_base_url}/api/v1/update/check"
                response = requests.get(
                    update_url,
                    params={'version': current_version},
                    timeout=10,
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    has_update = data.get('has_update', False)
                    latest_version = data.get('current_version', current_version)
                    download_url = data.get('download_url', '')
                    
                    if has_update:
                        msg = f"🔄 Update Available!\\n\\n"
                        msg += f"Current Version: {current_version}\\n"
                        msg += f"Latest Version: {latest_version}\\n\\n"
                        msg += f"This will download and install the update automatically.\\n"
                        msg += f"The application will restart after installation.\\n\\n"
                        msg += f"Continue?"
                        
                        if messagebox.askyesno("Update Available", msg):
                            self.install_update(download_url or f"{self.api_base_url}/download/client/linux")
                    else:
                        messagebox.showinfo("No Updates", 
                                          f"You're running the latest version!\\n\\n"
                                          f"Current Version: {current_version}")
                else:
                    messagebox.showerror("Update Check Failed", 
                                       f"Failed to check for updates.\\n"
                                       f"HTTP {response.status_code}")
            except requests.exceptions.ConnectionError:
                messagebox.showerror("Connection Error", 
                                   "Failed to connect to update server.\\n"
                                   "Please check your internet connection.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to check for updates: {e}")
        
        # Show checking message
        checking_window = tk.Toplevel(self.root)
        checking_window.title("Checking for Updates")
        checking_window.geometry("300x100")
        checking_window.configure(bg='#2b2b2b')
        checking_window.transient(self.root)
        checking_window.grab_set()
        
        tk.Label(checking_window, text="Checking for updates...", 
                bg='#2b2b2b', fg='#ffffff',
                font=('Arial', 12)).pack(pady=30)
        
        # Run check in background
        def close_and_check():
            checking_window.destroy()
            do_check()
        
        checking_window.after(500, close_and_check)
    
    def install_update(self, download_url):
        """Download and install update, then restart"""
        import threading
        import urllib.request
        
        def do_install():
            try:
                # Show progress window
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Installing Update")
                progress_window.geometry("400x150")
                progress_window.configure(bg='#2b2b2b')
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                status_label = tk.Label(progress_window, text="Downloading update...", 
                                        bg='#2b2b2b', fg='#ffffff',
                                        font=('Arial', 12))
                status_label.pack(pady=20)
                
                progress_bar = tk.ttk.Progressbar(progress_window, mode='indeterminate')
                progress_bar.pack(pady=10, padx=20, fill=tk.X)
                progress_bar.start()
                
                progress_window.update()
                
                # Download .deb package
                temp_dir = tempfile.mkdtemp()
                deb_file = Path(temp_dir) / 'phaze-vpn-update.deb'
                
                status_label.config(text="Downloading update package...")
                progress_window.update()
                
                # Download file
                urllib.request.urlretrieve(download_url, str(deb_file))
                
                status_label.config(text="Installing update (this may take a moment)...")
                progress_window.update()
                
                # Stop GUI gracefully
                self.root.quit()
                
                # Uninstall old version and install new
                subprocess.run(['sudo', 'apt-get', 'remove', '-y', 'phaze-vpn'], check=False)
                subprocess.run(['sudo', 'dpkg', '-i', str(deb_file)], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-f', '-y'], check=True)
                
                # Clean up
                shutil.rmtree(temp_dir)
                
                # Restart GUI
                subprocess.Popen(['phazevpn-gui'])
                
                progress_window.destroy()
                sys.exit(0)
                
            except Exception as e:
                messagebox.showerror("Update Failed", 
                                   f"Failed to install update:\\n{str(e)}\\n\\n"
                                   f"Please try downloading manually from:\\n{download_url}")
        
        # Run in background thread
        thread = threading.Thread(target=do_install, daemon=True)
        thread.start()'''

# Replace the method
if old_update_method in content:
    content = content.replace(old_update_method, new_update_method)
    with open(gui_file, 'w') as f:
        f.write(content)
    print(f"✅ Updated {gui_file}")
else:
    print("⚠️  Could not find exact match, manual update needed")

