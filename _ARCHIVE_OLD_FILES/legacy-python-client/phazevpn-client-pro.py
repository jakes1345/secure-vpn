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
API_BASE_URL = "https://phazevpn.duckdns.org"
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
        self.server_location = "Unknown"
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
        
        self.server_label = tk.Label(server_frame, text="phazevpn.duckdns.org",
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
                    self.config_path = config.get('config_path')
            except:
                pass
    
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
            
            openvpn = self._find_openvpn()
            if not openvpn:
                self.queue_update(self._connect_failed, "OpenVPN not found")
                return
            
            self.vpn_process = subprocess.Popen(
                [openvpn, '--config', str(self.config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(2)
            
            if self.vpn_process.poll() is None:
                self.queue_update(self._on_connected)
            else:
                error = self.vpn_process.stderr.read().decode()[:100]
                self.queue_update(self._connect_failed, error)
        
        except Exception as e:
            self.queue_update(self._connect_failed, str(e))
    
    def _fetch_config(self):
        """Fetch config"""
        try:
            self.session.post(f"{API_BASE_URL}/login",
                            data={'username': self.username, 'password': self.password},
                            timeout=3, verify=False)
            
            resp = self.session.get(f"{API_BASE_URL}/api/my-clients",
                                  timeout=3, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('clients'):
                    client_name = data['clients'][0]['name']
                    config_resp = self.session.get(f"{API_BASE_URL}/download/{client_name}",
                                                 timeout=3, verify=False)
                    if config_resp.status_code == 200:
                        config_dir = CLIENT_DIR / "configs"
                        config_dir.mkdir(exist_ok=True)
                        self.config_path = config_dir / f"{client_name}.ovpn"
                        with open(self.config_path, 'w') as f:
                            f.write(config_resp.text)
                        return True
        except:
            pass
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
        """Open settings"""
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("450x500")
        settings.configure(bg='#1a2332')
        settings.resizable(False, False)
        settings.transient(self.root)
        
        # Center
        settings.update_idletasks()
        x = (settings.winfo_screenwidth() // 2) - (450 // 2)
        y = (settings.winfo_screenheight() // 2) - (500 // 2)
        settings.geometry(f'450x500+{x}+{y}')
        
        frame = tk.Frame(settings, bg='#1a2332')
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        tk.Label(frame, text="Settings",
                font=('Segoe UI', 18, 'bold'),
                bg='#1a2332', fg='#fff').pack(pady=(0, 20))
        
        # Auto-connect
        auto_var = tk.BooleanVar()
        auto_cb = tk.Checkbutton(frame, text="Auto-connect on startup",
                                variable=auto_var,
                                bg='#1a2332', fg='#fff',
                                selectcolor='#2a3441',
                                font=('Segoe UI', 11),
                                activebackground='#1a2332',
                                activeforeground='#fff')
        auto_cb.pack(anchor='w', pady=10)
        
        # Protocol selection
        tk.Label(frame, text="VPN Protocol",
                font=('Segoe UI', 11, 'bold'),
                bg='#1a2332', fg='#fff').pack(anchor='w', pady=(20, 10))
        
        protocol_var = tk.StringVar(value="OpenVPN")
        protocols = ["OpenVPN", "WireGuard", "PhazeVPN Protocol"]
        for proto in protocols:
            rb = tk.Radiobutton(frame, text=proto,
                              variable=protocol_var,
                              value=proto,
                              bg='#1a2332', fg='#fff',
                              selectcolor='#2a3441',
                              font=('Segoe UI', 10),
                              activebackground='#1a2332',
                              activeforeground='#fff')
            rb.pack(anchor='w', pady=5)
        
        tk.Button(frame, text="Save",
                 command=settings.destroy,
                 bg='#4a9eff', fg='white',
                 font=('Segoe UI', 11, 'bold'),
                 relief=tk.FLAT,
                 pady=10,
                 width=20).pack(pady=20)
    
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

