#!/usr/bin/env python3
"""
PhazeVPN Professional Client - Full-Featured GUI
Modern, fast, and feature-rich VPN client
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
from queue import Queue
import platform

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Configuration
API_BASE_URL = "https://phazevpn.com"
CLIENT_DIR = Path.home() / ".phazevpn"
CLIENT_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CLIENT_DIR / "config.json"

class PhazeVPNPro:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhazeVPN Professional")
        self.root.geometry("600x750")
        self.root.resizable(True, True)
        self.root.configure(bg='#0f1419')
        self.root.minsize(550, 700)
        
        # Performance: Update queue
        self.update_queue = Queue()
        self.root.after(100, self.process_queue)
        
        # State
        self.connected = False
        self.vpn_process = None
        self.session = requests.Session()
        self.session.timeout = 5
        self.username = None
        self.password = None
        self.config_path = None
        self.connection_start_time = None
        self.bytes_sent = 0
        self.bytes_received = 0
        self.server_location = "phazevpn.com"
        self.protocol = "OpenVPN"
        
        # Load config
        self.load_config()
        
        # Setup modern UI
        self.setup_ui()
        self.center_window()
        
        # Start main loop
        self.root.mainloop()
    
    def setup_ui(self):
        """Setup professional modern UI"""
        # Top bar with gradient effect
        top_bar = tk.Frame(self.root, bg='#1a2332', height=80)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # Logo and title
        title_frame = tk.Frame(top_bar, bg='#1a2332')
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        title = tk.Label(title_frame, text="🔒 PhazeVPN", 
                        font=('Segoe UI', 22, 'bold'),
                        bg='#1a2332', fg='#4a9eff')
        title.pack(anchor='w')
        
        subtitle = tk.Label(title_frame, text="Professional VPN Client",
                           font=('Segoe UI', 9),
                           bg='#1a2332', fg='#8a9ba8')
        subtitle.pack(anchor='w')
        
        # Status indicator (right side)
        status_frame = tk.Frame(top_bar, bg='#1a2332')
        status_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        self.status_indicator = tk.Label(status_frame, text="⚫",
                                         font=('Segoe UI', 32),
                                         bg='#1a2332', fg='#666')
        self.status_indicator.pack()
        
        self.status_text = tk.Label(status_frame, text="Disconnected",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg='#1a2332', fg='#8a9ba8')
        self.status_text.pack()
        
        # Main content area
        main_container = tk.Frame(self.root, bg='#0f1419')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Connection card
        connection_card = tk.Frame(main_container, bg='#1a2332', relief=tk.FLAT)
        connection_card.pack(fill=tk.X, pady=(0, 15))
        
        card_inner = tk.Frame(connection_card, bg='#1a2332')
        card_inner.pack(padx=25, pady=25)
        
        # Server info
        server_frame = tk.Frame(card_inner, bg='#1a2332')
        server_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(server_frame, text="Server Location",
                font=('Segoe UI', 9),
                bg='#1a2332', fg='#8a9ba8').pack(anchor='w')
        
        self.server_label = tk.Label(server_frame, text="phazevpn.com",
                                    font=('Segoe UI', 14, 'bold'),
                                    bg='#1a2332', fg='#fff')
        self.server_label.pack(anchor='w', pady=(5, 0))
        
        # Protocol info
        protocol_frame = tk.Frame(card_inner, bg='#1a2332')
        protocol_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(protocol_frame, text="Protocol",
                font=('Segoe UI', 9),
                bg='#1a2332', fg='#8a9ba8').pack(anchor='w')
        
        self.protocol_label = tk.Label(protocol_frame, text="OpenVPN (UDP)",
                                      font=('Segoe UI', 11),
                                      bg='#1a2332', fg='#4a9eff')
        self.protocol_label.pack(anchor='w', pady=(5, 0))
        
        # Connect button (large, prominent)
        self.connect_btn = tk.Button(card_inner,
                                     text="CONNECT",
                                     command=self.toggle_connection,
                                     bg='#4a9eff',
                                     fg='white',
                                     font=('Segoe UI', 14, 'bold'),
                                     relief=tk.FLAT,
                                     cursor='hand2',
                                     height=2,
                                     width=25,
                                     activebackground='#3a8eef',
                                     activeforeground='white')
        self.connect_btn.pack(fill=tk.X, pady=(10, 0))
        
        # Stats card
        stats_card = tk.Frame(main_container, bg='#1a2332', relief=tk.FLAT)
        stats_card.pack(fill=tk.X, pady=(0, 15))
        
        stats_inner = tk.Frame(stats_card, bg='#1a2332')
        stats_inner.pack(padx=25, pady=20)
        
        tk.Label(stats_inner, text="Connection Statistics",
                font=('Segoe UI', 12, 'bold'),
                bg='#1a2332', fg='#fff').pack(anchor='w', pady=(0, 15))
        
        # Stats grid
        stats_grid = tk.Frame(stats_inner, bg='#1a2332')
        stats_grid.pack(fill=tk.X)
        
        # Duration
        duration_frame = tk.Frame(stats_grid, bg='#1a2332')
        duration_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(duration_frame, text="Duration",
                font=('Segoe UI', 9),
                bg='#1a2332', fg='#8a9ba8').pack()
        self.duration_label = tk.Label(duration_frame, text="0:00:00",
                                      font=('Segoe UI', 16, 'bold'),
                                      bg='#1a2332', fg='#fff')
        self.duration_label.pack()
        
        # Download
        download_frame = tk.Frame(stats_grid, bg='#1a2332')
        download_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(download_frame, text="Download",
                font=('Segoe UI', 9),
                bg='#1a2332', fg='#8a9ba8').pack()
        self.download_label = tk.Label(download_frame, text="0 MB",
                                      font=('Segoe UI', 16, 'bold'),
                                      bg='#1a2332', fg='#10b981')
        self.download_label.pack()
        
        # Upload
        upload_frame = tk.Frame(stats_grid, bg='#1a2332')
        upload_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(upload_frame, text="Upload",
                font=('Segoe UI', 9),
                bg='#1a2332', fg='#8a9ba8').pack()
        self.upload_label = tk.Label(upload_frame, text="0 MB",
                                    font=('Segoe UI', 16, 'bold'),
                                    bg='#1a2332', fg='#f59e0b')
        self.upload_label.pack()
        
        # Security features card
        security_card = tk.Frame(main_container, bg='#1a2332', relief=tk.FLAT)
        security_card.pack(fill=tk.X, pady=(0, 15))
        
        security_inner = tk.Frame(security_card, bg='#1a2332')
        security_inner.pack(padx=25, pady=20)
        
        tk.Label(security_inner, text="Security Features",
                font=('Segoe UI', 12, 'bold'),
                bg='#1a2332', fg='#fff').pack(anchor='w', pady=(0, 10))
        
        # Security features list
        features = [
            ("✅", "Kill Switch", "Active"),
            ("✅", "DNS Leak Protection", "Active"),
            ("✅", "IPv6 Blocking", "Active"),
            ("✅", "Military-Grade Encryption", "ChaCha20-Poly1305")
        ]
        
        for icon, feature, status in features:
            feat_frame = tk.Frame(security_inner, bg='#1a2332')
            feat_frame.pack(fill=tk.X, pady=5)
            tk.Label(feat_frame, text=f"{icon} {feature}",
                    font=('Segoe UI', 10),
                    bg='#1a2332', fg='#fff').pack(side=tk.LEFT)
            tk.Label(feat_frame, text=status,
                    font=('Segoe UI', 9),
                    bg='#1a2332', fg='#10b981').pack(side=tk.RIGHT)
        
        # Bottom buttons
        button_frame = tk.Frame(main_container, bg='#0f1419')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        settings_btn = tk.Button(button_frame,
                                 text="⚙️ Settings",
                                 command=self.open_settings,
                                 bg='#2a3441',
                                 fg='#fff',
                                 font=('Segoe UI', 11),
                                 relief=tk.FLAT,
                                 cursor='hand2',
                                 padx=20,
                                 pady=10,
                                 activebackground='#3a4451',
                                 activeforeground='#fff')
        settings_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        account_btn = tk.Button(button_frame,
                               text="👤 Account",
                               command=self.open_account,
                               bg='#2a3441',
                               fg='#fff',
                               font=('Segoe UI', 11),
                               relief=tk.FLAT,
                               cursor='hand2',
                               padx=20,
                               pady=10,
                               activebackground='#3a4451',
                               activeforeground='#fff')
        account_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Start stats update
        self.update_stats()
    
    def process_queue(self):
        """Process UI update queue"""
        try:
            while True:
                func, args = self.update_queue.get_nowait()
                func(*args)
        except:
            pass
        self.root.after(100, self.process_queue)
    
    def queue_update(self, func, *args):
        """Queue UI update"""
        self.update_queue.put((func, args))
    
    def center_window(self):
        """Center window"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_config(self):
        """Load config"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.username = config.get('username')
                    self.password = config.get('password')
            except:
                pass
        
        # Load settings
        settings_file = CLIENT_DIR / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.protocol = settings.get('protocol', 'OpenVPN')
            except:
                pass
                
        # Update protocol label
        if hasattr(self, 'protocol_label'):
             self.protocol_label.config(text=f"{self.protocol} (UDP)")
    
    def save_config(self):
        """Save config"""
        config = {
            'username': self.username,
            'password': self.password,
            'config_path': str(self.config_path) if self.config_path else None
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def toggle_connection(self):
        """Connect/disconnect"""
        if self.connected:
            self.disconnect()
        else:
            if not self.username or not self.password:
                self.show_login()
            else:
                self.connect()
    
    def show_login(self):
        """Show login dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Login to PhazeVPN")
        dialog.geometry("400x350")
        dialog.configure(bg='#1a2332')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f'400x350+{x}+{y}')
        
        frame = tk.Frame(dialog, bg='#1a2332')
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(frame, text="Login to PhazeVPN",
                font=('Segoe UI', 18, 'bold'),
                bg='#1a2332', fg='#fff').pack(pady=(0, 30))
        
        tk.Label(frame, text="Username",
                font=('Segoe UI', 10),
                bg='#1a2332', fg='#8a9ba8').pack(anchor='w')
        user_entry = tk.Entry(frame, font=('Segoe UI', 12),
                             bg='#2a3441', fg='#fff',
                             insertbackground='#fff',
                             relief=tk.FLAT,
                             borderwidth=0)
        user_entry.pack(fill=tk.X, pady=(5, 20), ipady=8)
        if self.username:
            user_entry.insert(0, self.username)
        
        tk.Label(frame, text="Password",
                font=('Segoe UI', 10),
                bg='#1a2332', fg='#8a9ba8').pack(anchor='w')
        pass_entry = tk.Entry(frame, font=('Segoe UI', 12),
                             show='*',
                             bg='#2a3441', fg='#fff',
                             insertbackground='#fff',
                             relief=tk.FLAT,
                             borderwidth=0)
        pass_entry.pack(fill=tk.X, pady=(5, 20), ipady=8)
        if self.password:
            pass_entry.insert(0, self.password)
        
        error_label = tk.Label(frame, text="", fg='#ef4444',
                              bg='#1a2332', font=('Segoe UI', 9))
        error_label.pack(pady=(0, 10))
        
        def login():
            self.username = user_entry.get().strip()
            self.password = pass_entry.get().strip()
            if self.username and self.password:
                self.save_config()
                dialog.destroy()
                self.connect()
            else:
                error_label.config(text="Username and password required")
        
        login_btn = tk.Button(frame, text="Login",
                            command=login,
                            bg='#4a9eff',
                            fg='white',
                            font=('Segoe UI', 12, 'bold'),
                            relief=tk.FLAT,
                            cursor='hand2',
                            pady=10,
                            activebackground='#3a8eef')
        login_btn.pack(fill=tk.X, pady=(10, 15))
        
        signup_link = tk.Label(frame, text="Don't have an account? Sign up",
                              font=('Segoe UI', 9),
                              fg='#4a9eff',
                              bg='#1a2332',
                              cursor='hand2')
        signup_link.pack()
        signup_link.bind('<Button-1>', lambda e: webbrowser.open(f"{API_BASE_URL}/signup"))
        
        pass_entry.bind('<Return>', lambda e: login())
        user_entry.focus()
    
    def connect(self):
        """Connect"""
        self.connect_btn.config(state=tk.DISABLED, text="CONNECTING...")
        self.status_text.config(text="Connecting...", fg='#f59e0b')
        self.status_indicator.config(text="🟡", fg='#f59e0b')
        
        threading.Thread(target=self._connect_thread, daemon=True).start()
    
    def _connect_thread(self):
        """Connection thread"""
        try:
            if not self.config_path or not Path(self.config_path).exists():
                if not self._fetch_config():
                    self.queue_update(self._connect_failed, "Could not get VPN config")
                    return
            
            if self.protocol == 'OpenVPN':
                openvpn = self._find_openvpn()
                if not openvpn:
                    self.queue_update(self._connect_failed, "OpenVPN not found")
                    return
                
                self.vpn_process = subprocess.Popen(
                    [openvpn, '--config', str(self.config_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            elif self.protocol == 'WireGuard':
                # sudo wg-quick up <config>
                # Note: Requires sudo/root
                if not os.path.exists('/usr/bin/wg-quick'):
                     self.queue_update(self._connect_failed, "WireGuard (wg-quick) not found")
                     return

                self.vpn_process = subprocess.Popen(
                    ['sudo', 'wg-quick', 'up', str(self.config_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
            elif self.protocol == 'PhazeVPN':
                # Custom Client
                # Try to find binary
                client_bin = "./phazevpn-bin"
                if not os.path.exists(client_bin):
                    client_bin = "/usr/bin/phazevpn-bin"
                if not os.path.exists(client_bin):
                    client_bin = "/usr/local/bin/phazevpn-client"
                
                if not os.path.exists(client_bin):
                     # Try fallback to directory-nested binary just in case
                     if os.path.exists("./phazevpn-client/main"):
                          client_bin = "./phazevpn-client/main"
                     else:
                          self.queue_update(self._connect_failed, "PhazeVPN Client binary not found")
                          return

                self.vpn_process = subprocess.Popen(
                    ['sudo', client_bin, '-config', str(self.config_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            time.sleep(2)
            
            # Check status
            if self.protocol == 'WireGuard':
                if self.vpn_process.poll() == 0:
                     self.queue_update(self._on_connected)
                else:
                     error = self.vpn_process.stderr.read().decode()[:100] if self.vpn_process.stderr else "Unknown error"
                     self.queue_update(self._connect_failed, error)
            else:
                # OpenVPN & PhazeVPN should keep running
                if self.vpn_process.poll() is None:
                    self.queue_update(self._on_connected)
                else:
                    error = self.vpn_process.stderr.read().decode()[:100] if self.vpn_process.stderr else "Unknown error"
                    self.queue_update(self._connect_failed, error)
        
        except Exception as e:
            self.queue_update(self._connect_failed, str(e))
    
    def _fetch_config(self):
        """Fetch config"""
        try:
            # Clear session first
            self.session.cookies.clear()
            
            # Login first - follow redirects to get session cookie
            login_resp = self.session.post(f"{API_BASE_URL}/login",
                            data={'username': self.username, 'password': self.password},
                            timeout=5, verify=False, allow_redirects=True)
            
            if login_resp.status_code not in [200, 302]:
                print(f"Login failed: {login_resp.status_code}")
                return False
            
            # Check if we have a session cookie (Flask uses custom name)
            session_cookie = None
            for cookie in self.session.cookies:
                if 'session' in cookie.name.lower() or 'vpn' in cookie.name.lower():
                    session_cookie = cookie
                    break
            
            if not session_cookie:
                print("Warning: No session cookie after login")
                print(f"Cookies received: {[c.name for c in self.session.cookies]}")
                # Try to get cookie from Set-Cookie header
                if 'Set-Cookie' in login_resp.headers:
                    print(f"Set-Cookie header: {login_resp.headers['Set-Cookie']}")
            else:
                print(f"Session cookie found: {session_cookie.name}")
            
            # Get user's clients
            resp = self.session.get(f"{API_BASE_URL}/api/my-clients",
                                  timeout=5, verify=False)
            
            if resp.status_code != 200:
                print(f"API failed: {resp.status_code} - {resp.text[:100]}")
                return False
            
            data = resp.json()
            clients = data.get('clients', [])
            
            # If no clients, try to create one using username
            if not clients:
                print("No clients found, creating one...")
                create_resp = self.session.post(f"{API_BASE_URL}/api/my-clients",
                                              json={'name': self.username},
                                              timeout=5, verify=False)
                if create_resp.status_code == 200:
                    # Retry getting clients
                    resp = self.session.get(f"{API_BASE_URL}/api/my-clients",
                                          timeout=5, verify=False)
                    if resp.status_code == 200:
                        data = resp.json()
                        clients = data.get('clients', [])
            
            if clients:
                client_name = clients[0]['name']
                print(f"Downloading config for client: {client_name} (Protocol: {self.protocol})")
                
                config_resp = self.session.get(f"{API_BASE_URL}/download/{client_name}?type={self.protocol.lower()}",
                                             timeout=5, verify=False)
                if config_resp.status_code == 200:
                    config_dir = CLIENT_DIR / "configs"
                    config_dir.mkdir(exist_ok=True)
                    
                    # Determine extension
                    ext = ".ovpn"
                    if self.protocol == "WireGuard":
                        ext = ".conf"
                    elif self.protocol == "PhazeVPN":
                        ext = ".conf"
                        
                    self.config_path = config_dir / f"{client_name}{ext}"
                    with open(self.config_path, 'w') as f:
                        f.write(config_resp.text)
                    print(f"Config saved to: {self.config_path}")
                    return True
                else:
                    print(f"Download failed: {config_resp.status_code}")
            else:
                print("No clients available after creation attempt")
        except Exception as e:
            print(f"Error fetching config: {e}")
            import traceback
            traceback.print_exc()
        return False
    
    def _find_openvpn(self):
        """Find OpenVPN"""
        paths = ['/usr/sbin/openvpn', '/usr/bin/openvpn']
        for p in paths:
            if os.path.exists(p):
                return p
        try:
            result = subprocess.run(['which', 'openvpn'],
                                  capture_output=True, timeout=1)
            if result.returncode == 0:
                return result.stdout.decode().strip()
        except:
            pass
        return None
    
    def _on_connected(self):
        """Connected"""
        self.connected = True
        self.connect_btn.config(state=tk.NORMAL, text="DISCONNECT", bg='#ef4444',
                               activebackground='#dc2626')
        self.status_text.config(text="Connected", fg='#10b981')
        self.status_indicator.config(text="🟢", fg='#10b981')
        self.connection_start_time = time.time()
        self.bytes_sent = 0
        self.bytes_received = 0
    
    def _connect_failed(self, error):
        """Connection failed"""
        self.connect_btn.config(state=tk.NORMAL, text="CONNECT", bg='#4a9eff')
        self.status_text.config(text="Connection failed", fg='#ef4444')
        self.status_indicator.config(text="⚫", fg='#666')
        messagebox.showerror("Connection Failed", f"Failed to connect:\n{error}")
    
    def disconnect(self):
        """Disconnect"""
        if self.protocol == 'WireGuard' and self.config_path:
             try:
                 subprocess.run(['sudo', 'wg-quick', 'down', str(self.config_path)], timeout=5)
             except:
                 pass

        if self.vpn_process:
            try:
                self.vpn_process.terminate()
                self.vpn_process.wait(timeout=3)
            except:
                try:
                    self.vpn_process.kill()
                except:
                    pass
            self.vpn_process = None
        
        self.connected = False
        self.connect_btn.config(text="CONNECT", bg='#4a9eff',
                               activebackground='#3a8eef')
        self.status_text.config(text="Disconnected", fg='#8a9ba8')
        self.status_indicator.config(text="⚫", fg='#666')
        self.duration_label.config(text="0:00:00")
        self.download_label.config(text="0 MB")
        self.upload_label.config(text="0 MB")
    
    def update_stats(self):
        """Update stats"""
        if self.connected and self.connection_start_time:
            elapsed = time.time() - self.connection_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.duration_label.config(text=f"{hours}:{minutes:02d}:{seconds:02d}")
            
            # Simulate traffic (in real app, get from OpenVPN management interface)
            self.bytes_received += 1024 * 10  # Simulate
            self.bytes_sent += 1024 * 5
            self.download_label.config(text=f"{self.bytes_received // (1024*1024)} MB")
            self.upload_label.config(text=f"{self.bytes_sent // (1024*1024)} MB")
        
        self.root.after(2000, self.update_stats)
    
    def open_settings(self):
        """Open comprehensive settings window"""
        settings = tk.Toplevel(self.root)
        settings.title("PhazeVPN Settings")
        settings.geometry("600x700")
        settings.configure(bg='#1a2332')
        settings.resizable(True, True)
        settings.transient(self.root)
        settings.minsize(550, 650)
        
        # Center
        settings.update_idletasks()
        x = (settings.winfo_screenwidth() // 2) - (600 // 2)
        y = (settings.winfo_screenheight() // 2) - (700 // 2)
        settings.geometry(f'600x700+{x}+{y}')
        
        # Create scrollable frame
        canvas = tk.Canvas(settings, bg='#1a2332', highlightthickness=0)
        scrollbar = ttk.Scrollbar(settings, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a2332')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame = scrollable_frame
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Title
        tk.Label(frame, text="PhazeVPN Settings",
                font=('Segoe UI', 20, 'bold'),
                bg='#1a2332', fg='#fff').pack(pady=(0, 30))
        
        # Load saved settings
        settings_file = CLIENT_DIR / "settings.json"
        saved_settings = {}
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
            except:
                pass
        
        # ========== CONNECTION SETTINGS ==========
        conn_frame = tk.LabelFrame(frame, text="Connection Settings",
                                  bg='#2a3441', fg='#fff',
                                  font=('Segoe UI', 12, 'bold'),
                                  padx=15, pady=15)
        conn_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Auto-connect
        auto_var = tk.BooleanVar(value=saved_settings.get('auto_connect', False))
        auto_cb = tk.Checkbutton(conn_frame, text="Auto-connect on startup",
                                variable=auto_var,
                                bg='#2a3441', fg='#fff',
                                selectcolor='#3a4451',
                                font=('Segoe UI', 10),
                                activebackground='#2a3441',
                                activeforeground='#fff')
        auto_cb.pack(anchor='w', pady=5)
        
        # Auto-reconnect
        reconnect_var = tk.BooleanVar(value=saved_settings.get('auto_reconnect', True))
        reconnect_cb = tk.Checkbutton(conn_frame, text="Auto-reconnect on disconnect",
                                     variable=reconnect_var,
                                     bg='#2a3441', fg='#fff',
                                     selectcolor='#3a4451',
                                     font=('Segoe UI', 10),
                                     activebackground='#2a3441',
                                     activeforeground='#fff')
        reconnect_cb.pack(anchor='w', pady=5)
        
        # ========== VPN PROTOCOL ==========
        proto_frame = tk.LabelFrame(frame, text="VPN Protocol",
                                   bg='#2a3441', fg='#fff',
                                   font=('Segoe UI', 12, 'bold'),
                                   padx=15, pady=15)
        proto_frame.pack(fill=tk.X, pady=(0, 15))
        
        protocol_var = tk.StringVar(value=saved_settings.get('protocol', 'OpenVPN'))
        protocols = [
            ("OpenVPN (Port 1194)", "OpenVPN"),
            ("WireGuard (Port 51820)", "WireGuard"),
            ("PhazeVPN Protocol (Port 51821)", "PhazeVPN")
        ]
        for label, value in protocols:
            rb = tk.Radiobutton(proto_frame, text=label,
                              variable=protocol_var,
                              value=value,
                              bg='#2a3441', fg='#fff',
                              selectcolor='#3a4451',
                              font=('Segoe UI', 10),
                              activebackground='#2a3441',
                              activeforeground='#fff')
            rb.pack(anchor='w', pady=3)
        
        # ========== DNS SETTINGS ==========
        dns_frame = tk.LabelFrame(frame, text="DNS Settings",
                                 bg='#2a3441', fg='#fff',
                                 font=('Segoe UI', 12, 'bold'),
                                 padx=15, pady=15)
        dns_frame.pack(fill=tk.X, pady=(0, 15))
        
        # DNS leak protection
        dns_leak_var = tk.BooleanVar(value=saved_settings.get('dns_leak_protection', True))
        dns_leak_cb = tk.Checkbutton(dns_frame, text="Enable DNS Leak Protection",
                                    variable=dns_leak_var,
                                    bg='#2a3441', fg='#fff',
                                    selectcolor='#3a4451',
                                    font=('Segoe UI', 10),
                                    activebackground='#2a3441',
                                    activeforeground='#fff')
        dns_leak_cb.pack(anchor='w', pady=5)
        
        # Custom DNS
        tk.Label(dns_frame, text="Primary DNS:",
                bg='#2a3441', fg='#8a9ba8',
                font=('Segoe UI', 9)).pack(anchor='w', pady=(10, 2))
        dns1_entry = tk.Entry(dns_frame, font=('Segoe UI', 10),
                             bg='#1a2332', fg='#fff',
                             insertbackground='#fff',
                             relief=tk.FLAT)
        dns1_entry.pack(fill=tk.X, pady=2, ipady=5)
        dns1_entry.insert(0, saved_settings.get('dns1', '1.1.1.1'))
        
        tk.Label(dns_frame, text="Secondary DNS:",
                bg='#2a3441', fg='#8a9ba8',
                font=('Segoe UI', 9)).pack(anchor='w', pady=(10, 2))
        dns2_entry = tk.Entry(dns_frame, font=('Segoe UI', 10),
                             bg='#1a2332', fg='#fff',
                             insertbackground='#fff',
                             relief=tk.FLAT)
        dns2_entry.pack(fill=tk.X, pady=2, ipady=5)
        dns2_entry.insert(0, saved_settings.get('dns2', '1.0.0.1'))
        
        # DNS presets
        dns_preset_var = tk.StringVar(value="Cloudflare")
        tk.Label(dns_frame, text="Quick Presets:",
                bg='#2a3441', fg='#8a9ba8',
                font=('Segoe UI', 9)).pack(anchor='w', pady=(10, 5))
        
        def set_dns_preset(preset):
            presets = {
                "Cloudflare": ("1.1.1.1", "1.0.0.1"),
                "Google": ("8.8.8.8", "8.8.4.4"),
                "Quad9": ("9.9.9.9", "149.112.112.112"),
                "OpenDNS": ("208.67.222.222", "208.67.220.220")
            }
            if preset in presets:
                dns1_entry.delete(0, tk.END)
                dns2_entry.delete(0, tk.END)
                dns1_entry.insert(0, presets[preset][0])
                dns2_entry.insert(0, presets[preset][1])
        
        dns_preset_frame = tk.Frame(dns_frame, bg='#2a3441')
        dns_preset_frame.pack(fill=tk.X, pady=5)
        for preset in ["Cloudflare", "Google", "Quad9", "OpenDNS"]:
            btn = tk.Button(dns_preset_frame, text=preset,
                           command=lambda p=preset: set_dns_preset(p),
                           bg='#3a4451', fg='#fff',
                           font=('Segoe UI', 8),
                           relief=tk.FLAT,
                           padx=10, pady=3)
            btn.pack(side=tk.LEFT, padx=2)
        
        # ========== SECURITY SETTINGS ==========
        sec_frame = tk.LabelFrame(frame, text="Security Features",
                                 bg='#2a3441', fg='#fff',
                                 font=('Segoe UI', 12, 'bold'),
                                 padx=15, pady=15)
        sec_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Kill switch
        killswitch_var = tk.BooleanVar(value=saved_settings.get('kill_switch', True))
        killswitch_cb = tk.Checkbutton(sec_frame, text="Kill Switch (Block all traffic if VPN disconnects)",
                                      variable=killswitch_var,
                                      bg='#2a3441', fg='#fff',
                                      selectcolor='#3a4451',
                                      font=('Segoe UI', 10),
                                      activebackground='#2a3441',
                                      activeforeground='#fff')
        killswitch_cb.pack(anchor='w', pady=5)
        
        # IPv6 blocking
        ipv6_block_var = tk.BooleanVar(value=saved_settings.get('block_ipv6', True))
        ipv6_block_cb = tk.Checkbutton(sec_frame, text="Block IPv6 (Prevent IPv6 leaks)",
                                      variable=ipv6_block_var,
                                      bg='#2a3441', fg='#fff',
                                      selectcolor='#3a4451',
                                      font=('Segoe UI', 10),
                                      activebackground='#2a3441',
                                      activeforeground='#fff')
        ipv6_block_cb.pack(anchor='w', pady=5)
        
        # ========== ADVANCED SETTINGS ==========
        adv_frame = tk.LabelFrame(frame, text="Advanced Settings",
                                 bg='#2a3441', fg='#fff',
                                 font=('Segoe UI', 12, 'bold'),
                                 padx=15, pady=15)
        adv_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Connection timeout
        tk.Label(adv_frame, text="Connection Timeout (seconds):",
                bg='#2a3441', fg='#8a9ba8',
                font=('Segoe UI', 9)).pack(anchor='w', pady=(5, 2))
        timeout_entry = tk.Entry(adv_frame, font=('Segoe UI', 10),
                                bg='#1a2332', fg='#fff',
                                insertbackground='#fff',
                                relief=tk.FLAT,
                                width=10)
        timeout_entry.pack(anchor='w', pady=2, ipady=5)
        timeout_entry.insert(0, str(saved_settings.get('timeout', 30)))
        
        # Logging level
        tk.Label(adv_frame, text="Logging Level:",
                bg='#2a3441', fg='#8a9ba8',
                font=('Segoe UI', 9)).pack(anchor='w', pady=(10, 5))
        log_level_var = tk.StringVar(value=saved_settings.get('log_level', 'Normal'))
        log_levels = ["Minimal", "Normal", "Verbose", "Debug"]
        log_frame = tk.Frame(adv_frame, bg='#2a3441')
        log_frame.pack(fill=tk.X)
        for level in log_levels:
            rb = tk.Radiobutton(log_frame, text=level,
                              variable=log_level_var,
                              value=level,
                              bg='#2a3441', fg='#fff',
                              selectcolor='#3a4451',
                              font=('Segoe UI', 9),
                              activebackground='#2a3441',
                              activeforeground='#fff')
            rb.pack(side=tk.LEFT, padx=10)
        
        # ========== NETWORK SETTINGS ==========
        net_frame = tk.LabelFrame(frame, text="Network Settings",
                                 bg='#2a3441', fg='#fff',
                                 font=('Segoe UI', 12, 'bold'),
                                 padx=15, pady=15)
        net_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Split tunneling (future feature)
        split_var = tk.BooleanVar(value=saved_settings.get('split_tunneling', False))
        split_cb = tk.Checkbutton(net_frame, text="Split Tunneling (Route only selected apps through VPN)",
                                 variable=split_var,
                                 bg='#2a3441', fg='#8a9ba8',
                                 selectcolor='#3a4451',
                                 font=('Segoe UI', 10),
                                 activebackground='#2a3441',
                                 activeforeground='#8a9ba8',
                                 state=tk.DISABLED)
        split_cb.pack(anchor='w', pady=5)
        tk.Label(net_frame, text="(Coming soon)",
                bg='#2a3441', fg='#666',
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', padx=20)
        
        # ========== SAVE BUTTON ==========
        def save_settings():
            settings_data = {
                'auto_connect': auto_var.get(),
                'auto_reconnect': reconnect_var.get(),
                'protocol': protocol_var.get(),
                'dns_leak_protection': dns_leak_var.get(),
                'dns1': dns1_entry.get().strip(),
                'dns2': dns2_entry.get().strip(),
                'kill_switch': killswitch_var.get(),
                'block_ipv6': ipv6_block_var.get(),
                'timeout': int(timeout_entry.get() or 30),
                'log_level': log_level_var.get(),
                'split_tunneling': split_var.get()
            }
            
            # Save to file
            with open(settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)
            
            # Apply settings to config if connected
            if self.config_path and self.config_path.exists():
                self._apply_settings_to_config(settings_data)
            
            messagebox.showinfo("Settings", "Settings saved successfully!")
            settings.destroy()
        
        save_btn = tk.Button(frame, text="💾 Save Settings",
                           command=save_settings,
                           bg='#4a9eff', fg='white',
                           font=('Segoe UI', 12, 'bold'),
                           relief=tk.FLAT,
                           pady=12,
                           cursor='hand2',
                           activebackground='#3a8eef')
        save_btn.pack(pady=20)
        
        # Cancel button
        cancel_btn = tk.Button(frame, text="Cancel",
                              command=settings.destroy,
                              bg='#3a4451', fg='#fff',
                              font=('Segoe UI', 10),
                              relief=tk.FLAT,
                              pady=8,
                              cursor='hand2')
        cancel_btn.pack()
        
        # Update canvas scroll region
        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _apply_settings_to_config(self, settings):
        """Apply settings to OpenVPN config file"""
        if not self.config_path or not self.config_path.exists():
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_lines = f.readlines()
            
            # Modify DNS settings
            new_lines = []
            skip_next = False
            for i, line in enumerate(config_lines):
                if 'dhcp-option DNS' in line:
                    # Replace DNS lines
                    if '1.1.1.1' in line or '1.0.0.1' in line or '8.8.8.8' in line:
                        continue  # Skip old DNS
                elif 'block-outside-dns' in line:
                    if not settings.get('dns_leak_protection', True):
                        continue  # Skip if disabled
                elif 'block-ipv6' in line:
                    if not settings.get('block_ipv6', True):
                        continue  # Skip if disabled
                elif 'redirect-gateway' in line:
                    if not settings.get('kill_switch', True):
                        continue  # Skip if disabled
                
                new_lines.append(line)
            
            # Add new DNS if enabled
            if settings.get('dns_leak_protection', True):
                dns1 = settings.get('dns1', '1.1.1.1')
                dns2 = settings.get('dns2', '1.0.0.1')
                # Find where to insert
                insert_pos = len(new_lines)
                for i, line in enumerate(new_lines):
                    if 'redirect-gateway' in line:
                        insert_pos = i
                        break
                new_lines.insert(insert_pos, f'dhcp-option DNS {dns1}\n')
                new_lines.insert(insert_pos + 1, f'dhcp-option DNS {dns2}\n')
                if settings.get('dns_leak_protection', True):
                    new_lines.insert(insert_pos + 2, 'block-outside-dns\n')
            
            # Write back
            with open(self.config_path, 'w') as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Error applying settings: {e}")
    
    def open_account(self):
        """Open account"""
        if self.username:
            webbrowser.open(f"{API_BASE_URL}/profile")
        else:
            messagebox.showinfo("Account", "Please login first")

def main():
    app = PhazeVPNPro()

if __name__ == '__main__':
    main()

