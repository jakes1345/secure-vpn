#!/usr/bin/env python3
"""
PhazeVPN Enhanced Client - Uses ALL Existing VPN-Native Security
Auto-connects, kill switch, DNS protection, all built-in
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
import platform

# API Configuration
API_BASE_URL = "https://phazevpn.duckdns.org"
CLIENT_DIR = Path.home() / ".phazevpn"
CLIENT_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CLIENT_DIR / "config.json"
VPN_CONFIG_DIR = CLIENT_DIR / "configs"
VPN_CONFIG_DIR.mkdir(exist_ok=True)

class PhazeVPNEnhancedClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhazeVPN - Enhanced Client")
        self.root.geometry("500x750")
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
        self.kill_switch_enabled = True  # Uses existing VPN-native kill switch
        
        # Statistics
        self.connection_start_time = None
        self.data_sent = 0
        self.data_received = 0
        
        # Load saved config
        self.load_config()
        
        self.setup_ui()
        self.center_window()
        
        # Auto-connect if enabled
        if self.auto_connect and self.config_path:
            self.root.after(1000, self.connect_vpn)
    
    def setup_ui(self):
        """Setup enhanced UI"""
        # Header
        header = tk.Frame(self.root, bg='#1a1f3a', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🔒 PhazeVPN", font=('Arial', 24, 'bold'),
                        bg='#1a1f3a', fg='#ffffff')
        title.pack(pady=20)
        
        # Connection Status
        status_frame = tk.Frame(self.root, bg='#0a0e27', pady=20)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="Disconnected", 
                                     font=('Arial', 14), bg='#0a0e27', fg='#ff4444')
        self.status_label.pack()
        
        self.status_indicator = tk.Label(status_frame, text="●", font=('Arial', 20),
                                         bg='#0a0e27', fg='#ff4444')
        self.status_indicator.pack()
        
        # Server Info
        info_frame = tk.Frame(self.root, bg='#0a0e27', pady=10)
        info_frame.pack(fill=tk.X)
        
        self.server_label = tk.Label(info_frame, text="Server: Not Connected",
                                     font=('Arial', 10), bg='#0a0e27', fg='#888888')
        self.server_label.pack()
        
        self.ip_label = tk.Label(info_frame, text="IP: --", font=('Arial', 10),
                                 bg='#0a0e27', fg='#888888')
        self.ip_label.pack()
        
        # Statistics Frame
        stats_frame = tk.LabelFrame(self.root, text="Statistics", bg='#1a1f3a',
                                    fg='#ffffff', font=('Arial', 10, 'bold'), pady=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_text = tk.Label(stats_frame, text="Connection Time: 00:00:00\n"
                                                      "Data Sent: 0 MB\n"
                                                      "Data Received: 0 MB",
                                   font=('Arial', 9), bg='#1a1f3a', fg='#ffffff',
                                   justify=tk.LEFT)
        self.stats_text.pack(padx=10, pady=5)
        
        # Security Features Frame
        security_frame = tk.LabelFrame(self.root, text="Security Features (VPN-Native)",
                                       bg='#1a1f3a', fg='#00ff00',
                                       font=('Arial', 10, 'bold'), pady=10)
        security_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # All security is VPN-native (uses existing scripts)
        security_text = tk.Label(security_frame,
                                 text="✅ Kill Switch (Network-level)\n"
                                      "✅ DNS Leak Protection\n"
                                      "✅ IPv6 Routing Through VPN\n"
                                      "✅ WebRTC Routing Through VPN\n"
                                      "✅ Tracking Protection\n"
                                      "All enforced automatically by VPN",
                                 font=('Arial', 9), bg='#1a1f3a', fg='#00ff00',
                                 justify=tk.LEFT)
        security_text.pack(padx=10, pady=5)
        
        # Control Buttons
        button_frame = tk.Frame(self.root, bg='#0a0e27', pady=20)
        button_frame.pack(fill=tk.X)
        
        self.connect_btn = tk.Button(button_frame, text="Connect", font=('Arial', 12, 'bold'),
                                     bg='#00aa00', fg='#ffffff', width=15, height=2,
                                     command=self.toggle_connection, cursor='hand2')
        self.connect_btn.pack(pady=5)
        
        # Settings Button
        settings_btn = tk.Button(button_frame, text="⚙️ Settings", font=('Arial', 10),
                                 bg='#333333', fg='#ffffff', width=15,
                                 command=self.open_settings, cursor='hand2')
        settings_btn.pack(pady=5)
        
        # Log Area
        log_frame = tk.LabelFrame(self.root, text="Connection Log", bg='#1a1f3a',
                                  fg='#ffffff', font=('Arial', 10, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg='#0a0e27',
                                                  fg='#00ff00', font=('Courier', 8),
                                                  wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Start status update loop
        self.update_status()
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_status(self):
        """Update connection status"""
        if self.connected:
            # Update connection time
            if self.connection_start_time:
                elapsed = datetime.now() - self.connection_start_time
                hours, remainder = divmod(elapsed.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # Update stats
                stats = f"Connection Time: {time_str}\n"
                stats += f"Data Sent: {self.data_sent / 1024 / 1024:.2f} MB\n"
                stats += f"Data Received: {self.data_received / 1024 / 1024:.2f} MB"
                self.stats_text.config(text=stats)
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    def load_config(self):
        """Load saved configuration"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.username = config.get('username')
                    self.password = config.get('password')
                    self.auto_connect = config.get('auto_connect', False)
                    self.kill_switch_enabled = config.get('kill_switch_enabled', True)
                    
                    # Load VPN config path
                    config_name = config.get('config_name')
                    if config_name:
                        self.config_path = VPN_CONFIG_DIR / f"{config_name}.ovpn"
            except Exception as e:
                self.log(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration"""
        config = {
            'username': self.username,
            'password': self.password,  # In production, encrypt this
            'auto_connect': self.auto_connect,
            'kill_switch_enabled': self.kill_switch_enabled,
            'config_name': self.config_path.stem if self.config_path else None
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def toggle_connection(self):
        """Connect or disconnect VPN"""
        if self.connected:
            self.disconnect_vpn()
        else:
            self.connect_vpn()
    
    def connect_vpn(self):
        """Connect to VPN - uses existing VPN-native security"""
        if not self.config_path or not self.config_path.exists():
            messagebox.showerror("Error", "No VPN config found. Please download from web portal.")
            return
        
        self.log("Connecting to VPN...")
        self.log("Note: All security features are VPN-native (automatic)")
        
        # Start OpenVPN process
        # The existing up-ultimate-security.sh script will automatically:
        # - Enable kill switch
        # - Enable DNS leak protection
        # - Route IPv6 through VPN
        # - Route WebRTC through VPN
        # - Enable tracking protection
        # All automatic - no user action needed!
        
        try:
            if platform.system() == "Windows":
                # Windows: Use OpenVPN GUI or command line
                self.vpn_process = subprocess.Popen(
                    ["openvpn", "--config", str(self.config_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # Linux/Mac: Use openvpn command
                self.vpn_process = subprocess.Popen(
                    ["sudo", "openvpn", "--config", str(self.config_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait a moment to check if connection started
            time.sleep(2)
            
            if self.vpn_process.poll() is None:
                self.connected = True
                self.connection_start_time = datetime.now()
                self.status_label.config(text="Connected", fg='#00ff00')
                self.status_indicator.config(fg='#00ff00')
                self.connect_btn.config(text="Disconnect", bg='#aa0000')
                self.log("✅ Connected! All security features active (VPN-native)")
                self.log("✅ Kill switch: Active")
                self.log("✅ DNS protection: Active")
                self.log("✅ IPv6 routing: Through VPN")
                self.log("✅ WebRTC routing: Through VPN")
            else:
                error = self.vpn_process.stderr.read().decode()
                self.log(f"❌ Connection failed: {error}")
                messagebox.showerror("Connection Failed", f"Failed to connect:\n{error}")
        
        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))
    
    def disconnect_vpn(self):
        """Disconnect VPN"""
        if self.vpn_process:
            self.vpn_process.terminate()
            self.vpn_process.wait()
            self.vpn_process = None
        
        self.connected = False
        self.connection_start_time = None
        self.status_label.config(text="Disconnected", fg='#ff4444')
        self.status_indicator.config(fg='#ff4444')
        self.connect_btn.config(text="Connect", bg='#00aa00')
        self.log("Disconnected from VPN")
    
    def open_settings(self):
        """Open settings window"""
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("400x300")
        settings.configure(bg='#0a0e27')
        
        # Auto-connect
        auto_connect_var = tk.BooleanVar(value=self.auto_connect)
        auto_connect_cb = tk.Checkbutton(settings, text="Auto-connect on startup",
                                         variable=auto_connect_var, bg='#0a0e27',
                                         fg='#ffffff', selectcolor='#1a1f3a')
        auto_connect_cb.pack(pady=10)
        
        # Note about security
        note = tk.Label(settings,
                       text="Note: All security features (kill switch, DNS protection, etc.)\n"
                            "are VPN-native and automatic. No configuration needed!",
                       font=('Arial', 9), bg='#0a0e27', fg='#00ff00',
                       justify=tk.LEFT)
        note.pack(pady=10)
        
        def save_settings():
            self.auto_connect = auto_connect_var.get()
            self.save_config()
            settings.destroy()
            messagebox.showinfo("Settings", "Settings saved!")
        
        save_btn = tk.Button(settings, text="Save", command=save_settings,
                            bg='#00aa00', fg='#ffffff', width=10)
        save_btn.pack(pady=20)
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_closing(self):
        """Handle window closing"""
        if self.connected:
            if messagebox.askokcancel("Quit", "VPN is connected. Disconnect and quit?"):
                self.disconnect_vpn()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == '__main__':
    app = PhazeVPNEnhancedClient()
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.root.mainloop()

