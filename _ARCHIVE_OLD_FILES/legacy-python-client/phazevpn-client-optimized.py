#!/usr/bin/env python3
"""
PhazeVPN Desktop Client - Optimized Performance Version
Fast, responsive, and smooth
"""

import tkinter as tk
from tkinter import ttk, messagebox
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

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Configuration
API_BASE_URL = "https://phazevpn.duckdns.org"
CLIENT_DIR = Path.home() / ".phazevpn"
CLIENT_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CLIENT_DIR / "config.json"

class PhazeVPNClientOptimized:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhazeVPN")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a1a')
        
        # Performance: Use update queue instead of frequent polling
        self.update_queue = Queue()
        self.root.after(100, self.process_queue)
        
        # State
        self.connected = False
        self.vpn_process = None
        self.session = requests.Session()
        self.session.timeout = 5  # Shorter timeout
        self.username = None
        self.password = None
        self.config_path = None
        self.connection_start_time = None
        self.last_update = 0
        self.update_interval = 2  # Update every 2 seconds instead of 1
        
        # Load config
        self.load_config()
        
        # Setup UI (simplified for performance)
        self.setup_ui()
        
        # Start main loop
        self.root.mainloop()
    
    def setup_ui(self):
        """Setup optimized UI"""
        # Header (simplified)
        header = tk.Frame(self.root, bg='#2a2a2a', height=60)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="PhazeVPN", 
                        font=('Arial', 18, 'bold'),
                        bg='#2a2a2a', fg='#4a9eff')
        title.pack(pady=15)
        
        # Main content
        main = tk.Frame(self.root, bg='#1a1a1a')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Status (simplified)
        self.status_label = tk.Label(main, text="Disconnected",
                                    font=('Arial', 14),
                                    bg='#1a1a1a', fg='#888')
        self.status_label.pack(pady=20)
        
        # Connect button
        self.connect_btn = tk.Button(main, 
                                     text="CONNECT",
                                     command=self.toggle_connection,
                                     bg='#4a9eff',
                                     fg='white',
                                     font=('Arial', 12, 'bold'),
                                     width=20,
                                     height=2,
                                     relief=tk.FLAT,
                                     cursor='hand2')
        self.connect_btn.pack(pady=20)
        
        # Stats (simplified, update less frequently)
        self.stats_label = tk.Label(main, text="Duration: 0:00",
                                   font=('Arial', 10),
                                   bg='#1a1a1a', fg='#666')
        self.stats_label.pack(pady=10)
        
        # Settings button
        settings_btn = tk.Button(main,
                                text="Settings",
                                command=self.open_settings,
                                bg='#333',
                                fg='#fff',
                                font=('Arial', 10),
                                relief=tk.FLAT,
                                width=15)
        settings_btn.pack(pady=10)
    
    def process_queue(self):
        """Process UI update queue (non-blocking)"""
        try:
            while True:
                func, args = self.update_queue.get_nowait()
                func(*args)
        except:
            pass
        self.root.after(100, self.process_queue)
    
    def queue_update(self, func, *args):
        """Queue UI update (thread-safe)"""
        self.update_queue.put((func, args))
    
    def load_config(self):
        """Load config (cached)"""
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
        """Show login (simplified)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Login")
        dialog.geometry("300x200")
        dialog.configure(bg='#2a2a2a')
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg='#2a2a2a')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="Username:", bg='#2a2a2a', fg='#fff').pack(anchor='w')
        user_entry = tk.Entry(frame, width=25)
        user_entry.pack(fill=tk.X, pady=5)
        if self.username:
            user_entry.insert(0, self.username)
        
        tk.Label(frame, text="Password:", bg='#2a2a2a', fg='#fff').pack(anchor='w', pady=(10,0))
        pass_entry = tk.Entry(frame, show='*', width=25)
        pass_entry.pack(fill=tk.X, pady=5)
        if self.password:
            pass_entry.insert(0, self.password)
        
        def login():
            self.username = user_entry.get().strip()
            self.password = pass_entry.get().strip()
            if self.username and self.password:
                self.save_config()
                dialog.destroy()
                self.connect()
        
        tk.Button(frame, text="Login", command=login,
                 bg='#4a9eff', fg='white',
                 width=15).pack(pady=15)
        
        pass_entry.bind('<Return>', lambda e: login())
        user_entry.focus()
    
    def connect(self):
        """Connect (optimized)"""
        self.connect_btn.config(state=tk.DISABLED, text="CONNECTING...")
        self.status_label.config(text="Connecting...", fg='#ffa500')
        
        # Run in thread (non-blocking)
        threading.Thread(target=self._connect_thread, daemon=True).start()
    
    def _connect_thread(self):
        """Connection thread (optimized)"""
        try:
            # Get config if needed
            if not self.config_path or not Path(self.config_path).exists():
                if not self._fetch_config():
                    self.queue_update(self._connect_failed, "No config available")
                    return
            
            # Find OpenVPN
            openvpn = self._find_openvpn()
            if not openvpn:
                self.queue_update(self._connect_failed, "OpenVPN not found")
                return
            
            # Start OpenVPN (non-blocking)
            self.vpn_process = subprocess.Popen(
                [openvpn, '--config', str(self.config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Check connection after delay
            time.sleep(2)
            
            if self.vpn_process.poll() is None:
                self.queue_update(self._on_connected)
            else:
                error = self.vpn_process.stderr.read().decode()[:100]
                self.queue_update(self._connect_failed, error)
        
        except Exception as e:
            self.queue_update(self._connect_failed, str(e))
    
    def _fetch_config(self):
        """Fetch config (cached)"""
        try:
            # Quick login
            self.session.post(f"{API_BASE_URL}/login",
                            data={'username': self.username, 'password': self.password},
                            timeout=3, verify=False)
            
            # Get clients
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
        """Find OpenVPN (cached)"""
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
        """Connected callback"""
        self.connected = True
        self.connect_btn.config(state=tk.NORMAL, text="DISCONNECT", bg='#ef4444')
        self.status_label.config(text="Connected", fg='#10b981')
        self.connection_start_time = time.time()
        self._start_stats_update()
    
    def _connect_failed(self, error):
        """Connection failed"""
        self.connect_btn.config(state=tk.NORMAL, text="CONNECT", bg='#4a9eff')
        self.status_label.config(text="Connection failed", fg='#f44')
        messagebox.showerror("Error", f"Failed to connect: {error}")
    
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
        self.connect_btn.config(text="CONNECT", bg='#4a9eff')
        self.status_label.config(text="Disconnected", fg='#888')
        self.stats_label.config(text="Duration: 0:00")
    
    def _start_stats_update(self):
        """Start stats update (optimized - less frequent)"""
        if self.connected and self.connection_start_time:
            elapsed = time.time() - self.connection_start_time
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            self.stats_label.config(text=f"Duration: {mins}:{secs:02d}")
            self.root.after(2000, self._start_stats_update)  # Update every 2 seconds
    
    def open_settings(self):
        """Settings (simplified)"""
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("300x200")
        settings.configure(bg='#2a2a2a')
        settings.transient(self.root)
        
        frame = tk.Frame(settings, bg='#2a2a2a')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="Settings", font=('Arial', 14, 'bold'),
                bg='#2a2a2a', fg='#fff').pack(pady=10)
        
        tk.Button(frame, text="Open Web Portal",
                 command=lambda: webbrowser.open(API_BASE_URL),
                 bg='#4a9eff', fg='white',
                 width=20).pack(pady=10)
        
        tk.Button(frame, text="Close",
                 command=settings.destroy,
                 bg='#666', fg='white',
                 width=20).pack(pady=10)

def main():
    app = PhazeVPNClientOptimized()

if __name__ == '__main__':
    main()

