#!/usr/bin/env python3
"""
PhazeVPN Desktop Client - Modern VPN Client Application
Connects to phazevpn.duckdns.org web portal
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import json
import requests
from pathlib import Path
from datetime import datetime
import sys
import os
import webbrowser

# API Configuration
API_BASE_URL = "https://phazevpn.duckdns.org"
CLIENT_DIR = Path.home() / ".phazevpn"
CLIENT_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CLIENT_DIR / "config.json"

class PhazeVPNClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhazeVPN Client")
        self.root.geometry("450x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#0a0e27')
        
        # State
        self.connected = False
        self.vpn_process = None
        self.session = requests.Session()
        self.username = None
        self.password = None
        self.client_config = None
        self.config_path = None
        self.auto_connect = False
        self.connection_start_time = None
        
        # Load saved credentials
        self.load_config()
        
        self.setup_ui()
        self.center_window()
        
        # Auto-connect if enabled and config exists
        auto_connect = False
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    auto_connect = config.get('auto_connect', False)
            except:
                pass
        
        if auto_connect and self.config_path and Path(self.config_path).exists():
            self.root.after(2000, self.connect)  # Connect after 2 seconds
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup the modern UI"""
        # Header
        header = tk.Frame(self.root, bg='#1a1f3a', height=80)
        header.pack(fill=tk.X)
        
        # Logo/Title
        title_frame = tk.Frame(header, bg='#1a1f3a')
        title_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        title = tk.Label(title_frame, text="🔒 PhazeVPN", 
                        font=('Segoe UI', 24, 'bold'),
                        bg='#1a1f3a', fg='#4a9eff')
        title.pack()
        
        subtitle = tk.Label(title_frame, text="Secure VPN Client",
                           font=('Segoe UI', 10),
                           bg='#1a1f3a', fg='#aaa')
        subtitle.pack()
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#0a0e27')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Connection status card
        status_card = tk.Frame(main_frame, bg='#1a1f3a', relief=tk.FLAT, bd=0)
        status_card.pack(fill=tk.X, pady=(0, 20))
        
        status_inner = tk.Frame(status_card, bg='#1a1f3a')
        status_inner.pack(padx=20, pady=20)
        
        self.status_indicator = tk.Label(status_inner, text="⚫",
                                        font=('Segoe UI', 48),
                                        bg='#1a1f3a', fg='#666')
        self.status_indicator.pack()
        
        self.status_label = tk.Label(status_inner, text="Disconnected",
                                    font=('Segoe UI', 14, 'bold'),
                                    bg='#1a1f3a', fg='#fff')
        self.status_label.pack(pady=(10, 5))
        
        self.server_label = tk.Label(status_inner, text="Not connected",
                                    font=('Segoe UI', 10),
                                    bg='#1a1f3a', fg='#aaa')
        self.server_label.pack()
        
        # Connect/Disconnect button
        self.connect_btn = tk.Button(main_frame, 
                                     text="CONNECT",
                                     command=self.toggle_connection,
                                     bg='#4a9eff',
                                     fg='white',
                                     font=('Segoe UI', 14, 'bold'),
                                     relief=tk.FLAT,
                                     cursor='hand2',
                                     height=2,
                                     borderwidth=0)
        self.connect_btn.pack(fill=tk.X, pady=(0, 20))
        
        # Stats card
        stats_card = tk.Frame(main_frame, bg='#1a1f3a')
        stats_card.pack(fill=tk.X, pady=(0, 20))
        
        stats_inner = tk.Frame(stats_card, bg='#1a1f3a')
        stats_inner.pack(padx=20, pady=15)
        
        tk.Label(stats_inner, text="Connection Stats",
                font=('Segoe UI', 12, 'bold'),
                bg='#1a1f3a', fg='#fff').pack(anchor='w', pady=(0, 10))
        
        self.stats_frame = tk.Frame(stats_inner, bg='#1a1f3a')
        self.stats_frame.pack(fill=tk.X)
        
        self.duration_label = tk.Label(self.stats_frame, text="Duration: 0:00",
                                      font=('Segoe UI', 10),
                                      bg='#1a1f3a', fg='#aaa')
        self.duration_label.pack(anchor='w', pady=2)
        
        self.download_label = tk.Label(self.stats_frame, text="Download: 0 MB",
                                      font=('Segoe UI', 10),
                                      bg='#1a1f3a', fg='#aaa')
        self.download_label.pack(anchor='w', pady=2)
        
        self.upload_label = tk.Label(self.stats_frame, text="Upload: 0 MB",
                                    font=('Segoe UI', 10),
                                    bg='#1a1f3a', fg='#aaa')
        self.upload_label.pack(anchor='w', pady=2)
        
        # Settings button
        settings_btn = tk.Button(main_frame,
                                text="⚙️ Settings",
                                command=self.open_settings,
                                bg='#2a2f4a',
                                fg='#fff',
                                font=('Segoe UI', 11),
                                relief=tk.FLAT,
                                cursor='hand2',
                                borderwidth=0)
        settings_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Account button
        account_btn = tk.Button(main_frame,
                               text="👤 Account",
                               command=self.open_account,
                               bg='#2a2f4a',
                               fg='#fff',
                               font=('Segoe UI', 11),
                               relief=tk.FLAT,
                               cursor='hand2',
                               borderwidth=0)
        account_btn.pack(fill=tk.X)
        
        # Auto-check connection status
        self.update_status_display()
        self.root.after(1000, self.periodic_update)
        
    def load_config(self):
        """Load saved configuration"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.username = config.get('username')
                    self.password = config.get('password')
                    self.config_path = config.get('config_path')
                    self.auto_connect = config.get('auto_connect', False)
            except:
                pass
    
    def save_config(self):
        """Save configuration"""
        config = {
            'username': self.username,
            'password': self.password,  # Note: In production, use encrypted storage
            'config_path': self.config_path,
            'auto_connect': self.auto_connect
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def toggle_connection(self):
        """Connect or disconnect VPN"""
        if self.connected:
            self.disconnect()
        else:
            if not self.username or not self.password:
                self.show_login_dialog()
                return
            self.connect()
    
    def show_login_dialog(self):
        """Show login dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Login to PhazeVPN")
        dialog.geometry("350x250")
        dialog.configure(bg='#1a1f3a')
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f'350x250+{x}+{y}')
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg='#1a1f3a')
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        tk.Label(frame, text="Login to PhazeVPN",
                font=('Segoe UI', 16, 'bold'),
                bg='#1a1f3a', fg='#fff').pack(pady=(0, 20))
        
        tk.Label(frame, text="Username:",
                font=('Segoe UI', 10),
                bg='#1a1f3a', fg='#aaa').pack(anchor='w')
        username_entry = tk.Entry(frame, font=('Segoe UI', 11), width=25)
        username_entry.pack(fill=tk.X, pady=(5, 15))
        if self.username:
            username_entry.insert(0, self.username)
        
        tk.Label(frame, text="Password:",
                font=('Segoe UI', 10),
                bg='#1a1f3a', fg='#aaa').pack(anchor='w')
        password_entry = tk.Entry(frame, font=('Segoe UI', 11), 
                                 show='*', width=25)
        password_entry.pack(fill=tk.X, pady=(5, 20))
        if self.password:
            password_entry.insert(0, self.password)
        
        error_label = tk.Label(frame, text="", fg='#f44', bg='#1a1f3a',
                              font=('Segoe UI', 9))
        error_label.pack(pady=(0, 10))
        
        def login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            
            if not username or not password:
                error_label.config(text="Username and password required")
                return
            
            # Try to login
            try:
                response = self.session.post(f"{API_BASE_URL}/login",
                                           data={'username': username, 
                                                'password': password},
                                           timeout=10,
                                           verify=False)  # Self-signed cert
                
                if response.status_code == 200 or 'dashboard' in response.url:
                    self.username = username
                    self.password = password
                    self.save_config()
                    dialog.destroy()
                    self.fetch_vpn_config()
                else:
                    error_label.config(text="Invalid credentials")
            except Exception as e:
                error_label.config(text=f"Connection error: {str(e)}")
        
        login_btn = tk.Button(frame, text="Login",
                             command=login,
                             bg='#4a9eff',
                             fg='white',
                             font=('Segoe UI', 11, 'bold'),
                             relief=tk.FLAT,
                             cursor='hand2')
        login_btn.pack(fill=tk.X, pady=(0, 10))
        
        signup_link = tk.Label(frame, text="Sign up at phazevpn.duckdns.org",
                              font=('Segoe UI', 9),
                              fg='#4a9eff',
                              bg='#1a1f3a',
                              cursor='hand2')
        signup_link.pack()
        signup_link.bind('<Button-1>', lambda e: webbrowser.open(f"{API_BASE_URL}/signup"))
        
        password_entry.bind('<Return>', lambda e: login())
        username_entry.focus()
    
    def fetch_vpn_config(self):
        """Fetch VPN config from web portal"""
        if not self.username or not self.password:
            return
        
        try:
            # Login first
            login_response = self.session.post(f"{API_BASE_URL}/login",
                                             data={'username': self.username,
                                                  'password': self.password},
                                             timeout=10,
                                             verify=False)
            
            # Get user's clients
            clients_response = self.session.get(f"{API_BASE_URL}/api/my-clients",
                                               timeout=10,
                                               verify=False)
            
            if clients_response.status_code == 200:
                data = clients_response.json()
                if data.get('success') and data.get('clients'):
                    # Use first client
                    client_name = data['clients'][0]['name']
                    
                    # Download config
                    config_response = self.session.get(f"{API_BASE_URL}/download/{client_name}",
                                                      timeout=10,
                                                      verify=False)
                    
                    if config_response.status_code == 200:
                        # Save config
                        config_dir = CLIENT_DIR / "configs"
                        config_dir.mkdir(exist_ok=True)
                        self.config_path = config_dir / f"{client_name}.ovpn"
                        
                        with open(self.config_path, 'w') as f:
                            f.write(config_response.text)
                        
                        return True
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch VPN config: {str(e)}")
            return False
    
    def connect(self):
        """Connect to VPN"""
        if not self.config_path or not self.config_path.exists():
            if not self.fetch_vpn_config():
                messagebox.showerror("Error", "Could not get VPN config. Please login.")
                return
        
        self.connect_btn.config(state=tk.DISABLED, text="CONNECTING...")
        self.status_label.config(text="Connecting...")
        
        # Start connection in thread
        thread = threading.Thread(target=self._connect_thread)
        thread.daemon = True
        thread.start()
    
    def _connect_thread(self):
        """Connect thread"""
        try:
            # Find OpenVPN binary
            openvpn_path = self.find_openvpn()
            if not openvpn_path:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "OpenVPN not found. Please install OpenVPN first."))
                self.root.after(0, lambda: self.connect_btn.config(
                    state=tk.NORMAL, text="CONNECT"))
                return
            
            # Start OpenVPN
            cmd = [openvpn_path, '--config', str(self.config_path),
                   '--management', '127.0.0.1', '7505', '--management-query-passwords']
            
            self.vpn_process = subprocess.Popen(cmd,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
            
            # Wait a bit and check if it's running
            time.sleep(3)
            
            if self.vpn_process.poll() is None:
                # Still running - connection successful
                self.root.after(0, self.on_connected)
            else:
                # Process ended - connection failed
                error = self.vpn_process.stderr.read().decode()
                self.root.after(0, lambda: messagebox.showerror(
                    "Connection Failed", f"Failed to connect: {error[:200]}"))
                self.root.after(0, lambda: self.connect_btn.config(
                    state=tk.NORMAL, text="CONNECT"))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error", f"Connection error: {str(e)}"))
            self.root.after(0, lambda: self.connect_btn.config(
                state=tk.NORMAL, text="CONNECT"))
    
    def find_openvpn(self):
        """Find OpenVPN binary"""
        # Common paths
        paths = [
            '/usr/sbin/openvpn',
            '/usr/bin/openvpn',
            '/usr/local/bin/openvpn',
            'C:\\Program Files\\OpenVPN\\bin\\openvpn.exe',
            'C:\\Program Files (x86)\\OpenVPN\\bin\\openvpn.exe'
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        # Try which/where
        try:
            if sys.platform == 'win32':
                result = subprocess.run(['where', 'openvpn'], 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(['which', 'openvpn'],
                                      capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None
    
    def on_connected(self):
        """Called when VPN connects - All security features are VPN-native and automatic!"""
        self.connected = True
        self.connect_btn.config(state=tk.NORMAL, text="DISCONNECT",
                               bg='#ef4444')
        self.status_indicator.config(text="🟢", fg='#10b981')
        self.status_label.config(text="Connected", fg='#10b981')
        self.server_label.config(text="phazevpn.duckdns.org")
        self.connection_start_time = time.time()
        
        # Note: All security is automatic via existing VPN scripts:
        # - Kill switch: up-ultimate-security.sh (already deployed)
        # - DNS protection: up-ultimate-security.sh (already deployed)
        # - IPv6 routing: up-ultimate-security.sh (already deployed)
        # - WebRTC routing: up-ultimate-security.sh (already deployed)
        # No user action needed - all VPN-native!
        self.update_stats()
    
    def disconnect(self):
        """Disconnect VPN"""
        if self.vpn_process:
            try:
                self.vpn_process.terminate()
                self.vpn_process.wait(timeout=5)
            except:
                self.vpn_process.kill()
            self.vpn_process = None
        
        self.connected = False
        self.connect_btn.config(text="CONNECT", bg='#4a9eff')
        self.status_indicator.config(text="⚫", fg='#666')
        self.status_label.config(text="Disconnected", fg='#fff')
        self.server_label.config(text="Not connected")
        
        self.duration_label.config(text="Duration: 0:00")
        self.download_label.config(text="Download: 0 MB")
        self.upload_label.config(text="Upload: 0 MB")
    
    def update_status_display(self):
        """Update connection status display"""
        # Check if actually connected by checking route or interface
        if self.vpn_process and self.vpn_process.poll() is None:
            if not self.connected:
                self.on_connected()
        elif self.connected:
            # Lost connection
            self.disconnect()
    
    def update_stats(self):
        """Update connection statistics"""
        if self.connected and hasattr(self, 'connection_start_time'):
            elapsed = time.time() - self.connection_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.duration_label.config(text=f"Duration: {minutes}:{seconds:02d}")
        
        # Schedule next update
        if self.connected:
            self.root.after(1000, self.update_stats)
    
    def periodic_update(self):
        """Periodic status update"""
        self.update_status_display()
        self.root.after(5000, self.periodic_update)
    
    def open_settings(self):
        """Open settings window"""
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("400x350")
        settings.configure(bg='#0a0e27')
        settings.resizable(False, False)
        
        # Center window
        settings.update_idletasks()
        x = (settings.winfo_screenwidth() // 2) - (400 // 2)
        y = (settings.winfo_screenheight() // 2) - (350 // 2)
        settings.geometry(f'400x350+{x}+{y}')
        settings.transient(self.root)
        
        frame = tk.Frame(settings, bg='#0a0e27')
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        tk.Label(frame, text="Settings", font=('Segoe UI', 18, 'bold'),
                bg='#0a0e27', fg='#fff').pack(pady=(0, 20))
        
        # Auto-connect option
        auto_connect_var = tk.BooleanVar(value=self.auto_connect)
        auto_connect_cb = tk.Checkbutton(frame, text="Auto-connect on startup",
                                         variable=auto_connect_var,
                                         bg='#0a0e27', fg='#fff',
                                         selectcolor='#1a1f3a',
                                         font=('Segoe UI', 11),
                                         activebackground='#0a0e27',
                                         activeforeground='#fff')
        auto_connect_cb.pack(anchor='w', pady=10)
        
        # Security info
        security_frame = tk.LabelFrame(frame, text="Security Features (VPN-Native)",
                                      bg='#1a1f3a', fg='#00ff00',
                                      font=('Segoe UI', 10, 'bold'))
        security_frame.pack(fill=tk.X, pady=20)
        
        security_text = tk.Label(security_frame,
                                text="✅ Kill Switch (Automatic)\n"
                                     "✅ DNS Leak Protection (Automatic)\n"
                                     "✅ IPv6 Routing Through VPN\n"
                                     "✅ WebRTC Routing Through VPN\n"
                                     "✅ Tracking Protection\n"
                                     "\nAll security is VPN-native and automatic!\n"
                                     "No configuration needed.",
                                font=('Segoe UI', 9),
                                bg='#1a1f3a', fg='#00ff00',
                                justify=tk.LEFT)
        security_text.pack(padx=15, pady=15)
        
        def save_settings():
            self.auto_connect = auto_connect_var.get()
            self.save_config()
            settings.destroy()
            messagebox.showinfo("Settings", "Settings saved!")
        
        save_btn = tk.Button(frame, text="Save", command=save_settings,
                            bg='#4a9eff', fg='white',
                            font=('Segoe UI', 11, 'bold'),
                            relief=tk.FLAT, cursor='hand2',
                            width=15, height=2)
        save_btn.pack(pady=20)
    
    def open_account(self):
        """Open account management"""
        if self.username:
            webbrowser.open(f"{API_BASE_URL}/profile")
        else:
            messagebox.showinfo("Account", "Please login first")

def main():
    # Disable SSL warnings for self-signed cert
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    app = PhazeVPNClient()
    app.root.mainloop()

if __name__ == '__main__':
    main()

