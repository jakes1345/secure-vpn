#!/usr/bin/env python3
"""
PhazeVPN Unified Client & Dashboard
Modern, all-in-one VPN client with integrated dashboard
Matches website design, supports Tor integration, all VPN modes

Copyright (c) 2024 PhazeVPN. All Rights Reserved.
Proprietary and Confidential. Unauthorized copying, modification,
distribution, or use of this software is strictly prohibited.
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
import platform
import socket
import struct

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_BASE_URL = "https://phazevpn.duckdns.org"
CLIENT_DIR = Path.home() / ".phazevpn"
CLIENT_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CLIENT_DIR / "config.json"
LOG_FILE = CLIENT_DIR / "phazevpn.log"

# Modern color scheme matching website
COLORS = {
    'bg_primary': '#0f172a',
    'bg_secondary': '#1e293b',
    'bg_card': '#1e293b',
    'bg_hover': '#334155',
    'primary': '#4a9eff',
    'primary_dark': '#3a8eef',
    'secondary': '#10b981',
    'text_primary': '#f1f5f9',
    'text_secondary': '#cbd5e1',
    'text_muted': '#94a3b8',
    'danger': '#ef4444',
    'success': '#10b981',
    'warning': '#f59e0b',
    'border': '#334155',
}

class TorManager:
    """Manages Tor integration for ghost mode"""
    
    def __init__(self):
        self.tor_process = None
        self.tor_enabled = False
        self.tor_port = 9050
        self.socks_port = 9050
        
    def check_tor_installed(self):
        """Check if Tor is installed"""
        try:
            subprocess.run(['which', 'tor'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def install_tor(self):
        """Install Tor via package manager"""
        if platform.system() == 'Linux':
            try:
                subprocess.run(['sudo', 'apt-get', 'update'], check=True, capture_output=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tor'], check=True, capture_output=True)
                return True
            except:
                return False
        return False
    
    def start_tor(self):
        """Start Tor service"""
        if not self.check_tor_installed():
            if not self.install_tor():
                return False
        
        try:
            # Start Tor in background
            self.tor_process = subprocess.Popen(
                ['tor'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Wait for Tor to start
            self.tor_enabled = True
            return True
        except Exception as e:
            print(f"Tor start error: {e}")
            return False
    
    def stop_tor(self):
        """Stop Tor service"""
        if self.tor_process:
            try:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=5)
            except:
                self.tor_process.kill()
            self.tor_process = None
        self.tor_enabled = False
    
    def get_tor_socks(self):
        """Get Tor SOCKS proxy address"""
        if self.tor_enabled:
            return f"socks5://127.0.0.1:{self.socks_port}"
        return None

class PhazeVPNUnified:
    """Unified PhazeVPN Client & Dashboard"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhazeVPN - Just Phaze Right On By")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['bg_primary'])
        self.root.minsize(800, 600)
        
        # State
        self.connected = False
        self.vpn_process = None
        self.session = requests.Session()
        self.username = None
        self.config_path = None
        self.vpn_mode = "normal"  # normal, semi_ghost, full_ghost, tor_ghost
        self.tor_manager = TorManager()
        
        # Stats
        self.connection_start_time = None
        self.bytes_sent = 0
        self.bytes_received = 0
        self.current_ip = "Not connected"
        self.server_location = "phazevpn.duckdns.org"
        
        # Update queue
        self.update_queue = Queue()
        self.root.after(100, self.process_queue)
        
        # Load config
        self.load_config()
        
        # Setup UI
        self.setup_ui()
        self.center_window()
        
        # Start stats update
        self.update_stats()
        
        # Main loop
        self.root.mainloop()
    
    def setup_ui(self):
        """Setup modern unified UI matching website"""
        # Top header with gradient
        header = tk.Frame(self.root, bg=COLORS['bg_secondary'], height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Logo and title
        title_frame = tk.Frame(header, bg=COLORS['bg_secondary'])
        title_frame.pack(side=tk.LEFT, padx=25, pady=20)
        
        tk.Label(title_frame, text="🔒 PhazeVPN", 
                font=('Segoe UI', 24, 'bold'),
                bg=COLORS['bg_secondary'], fg=COLORS['primary']).pack(anchor='w')
        
        tk.Label(title_frame, text='"Just Phaze Right On By - Nothing Will Notice You At All"',
                font=('Segoe UI', 9),
                bg=COLORS['bg_secondary'], fg=COLORS['text_muted']).pack(anchor='w', pady=(2, 0))
        
        # Status indicator (right)
        status_frame = tk.Frame(header, bg=COLORS['bg_secondary'])
        status_frame.pack(side=tk.RIGHT, padx=25, pady=20)
        
        self.status_indicator = tk.Label(status_frame, text="⚫",
                                         font=('Segoe UI', 36),
                                         bg=COLORS['bg_secondary'], fg='#666')
        self.status_indicator.pack()
        
        self.status_text = tk.Label(status_frame, text="Disconnected",
                                   font=('Segoe UI', 11, 'bold'),
                                   bg=COLORS['bg_secondary'], fg=COLORS['text_muted'])
        self.status_text.pack()
        
        # Main container with tabs
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook (tabs)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=COLORS['bg_primary'], borderwidth=0)
        style.configure('TNotebook.Tab', background=COLORS['bg_secondary'], foreground=COLORS['text_primary'],
                       padding=[20, 10], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', COLORS['bg_card'])],
                 foreground=[('selected', COLORS['primary'])])
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Connection
        self.connection_tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(self.connection_tab, text="🔌 Connect")
        self.setup_connection_tab()
        
        # Tab 2: Dashboard
        self.dashboard_tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(self.dashboard_tab, text="📊 Dashboard")
        self.setup_dashboard_tab()
        
        # Tab 3: Settings
        self.settings_tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(self.settings_tab, text="⚙️ Settings")
        self.setup_settings_tab()
        
        # Tab 4: Logs
        self.logs_tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(self.logs_tab, text="📋 Logs")
        self.setup_logs_tab()
    
    def setup_connection_tab(self):
        """Setup connection tab"""
        # Connection card
        card = tk.Frame(self.connection_tab, bg=COLORS['bg_card'], relief=tk.FLAT)
        card.pack(fill=tk.X, pady=(0, 15))
        
        inner = tk.Frame(card, bg=COLORS['bg_card'])
        inner.pack(padx=25, pady=25)
        
        # Server info
        tk.Label(inner, text="Server Location",
                font=('Segoe UI', 9),
                bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w')
        
        self.server_label = tk.Label(inner, text=self.server_location,
                                    font=('Segoe UI', 16, 'bold'),
                                    bg=COLORS['bg_card'], fg=COLORS['text_primary'])
        self.server_label.pack(anchor='w', pady=(5, 0))
        
        # Current IP
        ip_frame = tk.Frame(inner, bg=COLORS['bg_card'])
        ip_frame.pack(fill=tk.X, pady=(15, 20))
        
        tk.Label(ip_frame, text="Your IP",
                font=('Segoe UI', 9),
                bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w')
        
        self.ip_label = tk.Label(ip_frame, text=self.current_ip,
                                font=('Segoe UI', 14),
                                bg=COLORS['bg_card'], fg=COLORS['primary'])
        self.ip_label.pack(anchor='w', pady=(5, 0))
        
        # VPN Mode selector
        mode_frame = tk.Frame(inner, bg=COLORS['bg_card'])
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(mode_frame, text="VPN Mode",
                font=('Segoe UI', 9),
                bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w')
        
        mode_container = tk.Frame(mode_frame, bg=COLORS['bg_card'])
        mode_container.pack(fill=tk.X, pady=(10, 0))
        
        self.mode_var = tk.StringVar(value=self.vpn_mode)
        
        modes = [
            ("🟢 Normal", "normal", "Fast, secure"),
            ("🟡 Semi Ghost", "semi_ghost", "Enhanced privacy"),
            ("🔴 Full Ghost", "full_ghost", "Maximum stealth"),
            ("👻 Tor Ghost", "tor_ghost", "Complete anonymity"),
        ]
        
        for text, value, desc in modes:
            btn = tk.Radiobutton(mode_container, text=text,
                                variable=self.mode_var, value=value,
                                font=('Segoe UI', 10),
                                bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                                selectcolor=COLORS['bg_card'],
                                activebackground=COLORS['bg_hover'],
                                activeforeground=COLORS['text_primary'],
                                command=lambda v=value: self.on_mode_change(v))
            btn.pack(anchor='w', pady=2)
            
            tk.Label(mode_container, text=f"  {desc}",
                    font=('Segoe UI', 8),
                    bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w', padx=(25, 0))
        
        # Connect button
        self.connect_btn = tk.Button(inner,
                                     text="CONNECT",
                                     command=self.toggle_connection,
                                     bg=COLORS['primary'],
                                     fg='white',
                                     font=('Segoe UI', 14, 'bold'),
                                     relief=tk.FLAT,
                                     cursor='hand2',
                                     height=2,
                                     padx=40,
                                     activebackground=COLORS['primary_dark'])
        self.connect_btn.pack(pady=(10, 0), fill=tk.X)
        
        # Quick stats card
        stats_card = tk.Frame(self.connection_tab, bg=COLORS['bg_card'])
        stats_card.pack(fill=tk.X, pady=(0, 15))
        
        stats_inner = tk.Frame(stats_card, bg=COLORS['bg_card'])
        stats_inner.pack(padx=25, pady=20)
        
        tk.Label(stats_inner, text="Connection Stats",
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))
        
        stats_grid = tk.Frame(stats_inner, bg=COLORS['bg_card'])
        stats_grid.pack(fill=tk.X)
        
        # Duration
        duration_frame = tk.Frame(stats_grid, bg=COLORS['bg_card'])
        duration_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(duration_frame, text="Duration",
                font=('Segoe UI', 9),
                bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack()
        self.duration_label = tk.Label(duration_frame, text="00:00:00",
                                       font=('Segoe UI', 14, 'bold'),
                                       bg=COLORS['bg_card'], fg=COLORS['text_primary'])
        self.duration_label.pack()
        
        # Data transferred
        data_frame = tk.Frame(stats_grid, bg=COLORS['bg_card'])
        data_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(data_frame, text="Data Transferred",
                font=('Segoe UI', 9),
                bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack()
        self.data_label = tk.Label(data_frame, text="0 MB",
                                   font=('Segoe UI', 14, 'bold'),
                                   bg=COLORS['bg_card'], fg=COLORS['text_primary'])
        self.data_label.pack()
    
    def setup_dashboard_tab(self):
        """Setup dashboard tab with stats"""
        # Dashboard content
        scroll_frame = tk.Frame(self.dashboard_tab, bg=COLORS['bg_primary'])
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Stats grid
        stats_grid = tk.Frame(scroll_frame, bg=COLORS['bg_primary'])
        stats_grid.pack(fill=tk.X, pady=(0, 15))
        
        # Create stat cards
        stat_cards = [
            ("Connection Status", "Disconnected", COLORS['danger']),
            ("Current Mode", "Normal", COLORS['primary']),
            ("Server Latency", "N/A", COLORS['text_muted']),
            ("Bandwidth", "0 MB/s", COLORS['success']),
        ]
        
        for title, value, color in stat_cards:
            card = tk.Frame(stats_grid, bg=COLORS['bg_card'], relief=tk.FLAT)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
            
            inner = tk.Frame(card, bg=COLORS['bg_card'])
            inner.pack(padx=20, pady=20)
            
            tk.Label(inner, text=title,
                    font=('Segoe UI', 9),
                    bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor='w')
            
            tk.Label(inner, text=value,
                    font=('Segoe UI', 16, 'bold'),
                    bg=COLORS['bg_card'], fg=color).pack(anchor='w', pady=(5, 0))
        
        # Connection history placeholder
        history_card = tk.Frame(scroll_frame, bg=COLORS['bg_card'])
        history_card.pack(fill=tk.BOTH, expand=True)
        
        history_inner = tk.Frame(history_card, bg=COLORS['bg_card'])
        history_inner.pack(padx=25, pady=25, fill=tk.BOTH, expand=True)
        
        tk.Label(history_inner, text="Connection History",
                font=('Segoe UI', 14, 'bold'),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))
        
        self.history_text = tk.Text(history_inner,
                                    bg=COLORS['bg_primary'],
                                    fg=COLORS['text_primary'],
                                    font=('Consolas', 10),
                                    relief=tk.FLAT,
                                    wrap=tk.WORD,
                                    height=10)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        self.history_text.insert('1.0', "No connection history yet.\n")
        self.history_text.config(state=tk.DISABLED)
    
    def setup_settings_tab(self):
        """Setup settings tab"""
        scroll_frame = tk.Frame(self.settings_tab, bg=COLORS['bg_primary'])
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Account settings
        account_card = tk.Frame(scroll_frame, bg=COLORS['bg_card'])
        account_card.pack(fill=tk.X, pady=(0, 15))
        
        account_inner = tk.Frame(account_card, bg=COLORS['bg_card'])
        account_inner.pack(padx=25, pady=25)
        
        tk.Label(account_inner, text="Account Settings",
                font=('Segoe UI', 14, 'bold'),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))
        
        # Username
        user_frame = tk.Frame(account_inner, bg=COLORS['bg_card'])
        user_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(user_frame, text="Username",
                font=('Segoe UI', 10),
                bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w')
        
        self.username_entry = tk.Entry(user_frame,
                                       font=('Segoe UI', 11),
                                       bg=COLORS['bg_hover'],
                                       fg=COLORS['text_primary'],
                                       insertbackground=COLORS['text_primary'],
                                       relief=tk.FLAT)
        self.username_entry.pack(fill=tk.X, pady=(5, 0), ipady=8)
        if self.username:
            self.username_entry.insert(0, self.username)
        
        # Config file
        config_frame = tk.Frame(account_inner, bg=COLORS['bg_card'])
        config_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(config_frame, text="VPN Config File",
                font=('Segoe UI', 10),
                bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(anchor='w')
        
        config_file_frame = tk.Frame(config_frame, bg=COLORS['bg_card'])
        config_file_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.config_entry = tk.Entry(config_file_frame,
                                     font=('Segoe UI', 10),
                                     bg=COLORS['bg_hover'],
                                     fg=COLORS['text_primary'],
                                     insertbackground=COLORS['text_primary'],
                                     relief=tk.FLAT)
        self.config_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        if self.config_path:
            self.config_entry.insert(0, str(self.config_path))
        
        tk.Button(config_file_frame, text="Browse",
                 command=self.browse_config,
                 bg=COLORS['bg_hover'],
                 fg=COLORS['text_primary'],
                 font=('Segoe UI', 10),
                 relief=tk.FLAT,
                 padx=15,
                 cursor='hand2').pack(side=tk.RIGHT, padx=(10, 0))
        
        # Advanced settings
        advanced_card = tk.Frame(scroll_frame, bg=COLORS['bg_card'])
        advanced_card.pack(fill=tk.X, pady=(0, 15))
        
        advanced_inner = tk.Frame(advanced_card, bg=COLORS['bg_card'])
        advanced_inner.pack(padx=25, pady=25)
        
        tk.Label(advanced_inner, text="Advanced Settings",
                font=('Segoe UI', 14, 'bold'),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 15))
        
        # Auto-connect
        self.auto_connect_var = tk.BooleanVar()
        auto_connect = tk.Checkbutton(advanced_inner,
                                      text="Auto-connect on startup",
                                      variable=self.auto_connect_var,
                                      font=('Segoe UI', 10),
                                      bg=COLORS['bg_card'],
                                      fg=COLORS['text_primary'],
                                      selectcolor=COLORS['bg_card'],
                                      activebackground=COLORS['bg_hover'],
                                      activeforeground=COLORS['text_primary'])
        auto_connect.pack(anchor='w', pady=5)
        
        # Kill switch
        self.kill_switch_var = tk.BooleanVar(value=True)
        kill_switch = tk.Checkbutton(advanced_inner,
                                     text="Kill switch (block internet if VPN disconnects)",
                                     variable=self.kill_switch_var,
                                     font=('Segoe UI', 10),
                                     bg=COLORS['bg_card'],
                                     fg=COLORS['text_primary'],
                                     selectcolor=COLORS['bg_card'],
                                     activebackground=COLORS['bg_hover'],
                                     activeforeground=COLORS['text_primary'])
        kill_switch.pack(anchor='w', pady=5)
        
        # Save button
        tk.Button(advanced_inner, text="Save Settings",
                 command=self.save_settings,
                 bg=COLORS['primary'],
                 fg='white',
                 font=('Segoe UI', 11, 'bold'),
                 relief=tk.FLAT,
                 padx=30,
                 pady=10,
                 cursor='hand2').pack(anchor='w', pady=(15, 0))
    
    def setup_logs_tab(self):
        """Setup logs tab"""
        logs_inner = tk.Frame(self.logs_tab, bg=COLORS['bg_primary'])
        logs_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(logs_inner, text="Connection Logs",
                font=('Segoe UI', 14, 'bold'),
                bg=COLORS['bg_primary'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 10))
        
        self.logs_text = tk.Text(logs_inner,
                                bg=COLORS['bg_card'],
                                fg=COLORS['text_primary'],
                                font=('Consolas', 9),
                                relief=tk.FLAT,
                                wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(self.logs_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.logs_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.logs_text.yview)
        
        self.log("PhazeVPN Unified Client started")
        self.log(f"System: {platform.system()} {platform.release()}")
    
    def on_mode_change(self, mode):
        """Handle VPN mode change"""
        self.vpn_mode = mode
        if mode == "tor_ghost" and not self.tor_manager.tor_enabled:
            self.log("Starting Tor for ghost mode...")
            if not self.tor_manager.start_tor():
                messagebox.showerror("Tor Error", "Failed to start Tor. Install it with: sudo apt-get install tor")
                self.mode_var.set("normal")
                self.vpn_mode = "normal"
    
    def toggle_connection(self):
        """Toggle VPN connection"""
        if self.connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connect to VPN"""
        if not self.config_path or not Path(self.config_path).exists():
            messagebox.showerror("Error", "Please select a VPN config file in Settings")
            return
        
        self.log(f"Connecting with {self.vpn_mode} mode...")
        self.connect_btn.config(text="CONNECTING...", state=tk.DISABLED)
        
        # Start connection in thread
        thread = threading.Thread(target=self._connect_thread, daemon=True)
        thread.start()
    
    def _connect_thread(self):
        """Connection thread"""
        try:
            # Build OpenVPN command
            cmd = ['sudo', 'openvpn', '--config', str(self.config_path)]
            
            # Add mode-specific options
            if self.vpn_mode == "tor_ghost":
                # Route through Tor
                cmd.extend(['--socks-proxy', '127.0.0.1', '9050'])
            
            # Start VPN process
            self.vpn_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.connection_start_time = time.time()
            self.connected = True
            
            self.root.after(0, self._on_connected)
            
            # Monitor process
            for line in self.vpn_process.stdout:
                self.log(f"VPN: {line.strip()}")
                if "Initialization Sequence Completed" in line:
                    self.root.after(0, lambda: self.update_status_indicator(True))
                    
        except Exception as e:
            self.log(f"Connection error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to connect: {e}"))
            self.root.after(0, self._on_disconnected)
    
    def disconnect(self):
        """Disconnect from VPN"""
        if self.vpn_process:
            try:
                self.vpn_process.terminate()
                self.vpn_process.wait(timeout=5)
            except:
                self.vpn_process.kill()
            self.vpn_process = None
        
        self.connected = False
        self.connection_start_time = None
        self._on_disconnected()
    
    def _on_connected(self):
        """Called when connected"""
        self.connect_btn.config(text="DISCONNECT", state=tk.NORMAL, bg=COLORS['danger'])
        self.update_status_indicator(True)
        self.log("Connected to VPN")
        self.update_ip()
    
    def _on_disconnected(self):
        """Called when disconnected"""
        self.connect_btn.config(text="CONNECT", state=tk.NORMAL, bg=COLORS['primary'])
        self.update_status_indicator(False)
        self.log("Disconnected from VPN")
        self.current_ip = "Not connected"
        self.ip_label.config(text=self.current_ip)
    
    def update_status_indicator(self, connected):
        """Update status indicator"""
        if connected:
            self.status_indicator.config(text="🟢", fg=COLORS['success'])
            self.status_text.config(text="Connected", fg=COLORS['success'])
        else:
            self.status_indicator.config(text="⚫", fg='#666')
            self.status_text.config(text="Disconnected", fg=COLORS['text_muted'])
    
    def update_stats(self):
        """Update connection statistics"""
        if self.connected and self.connection_start_time:
            # Duration
            elapsed = time.time() - self.connection_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.duration_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Data (placeholder - would need actual stats)
            total_mb = (self.bytes_sent + self.bytes_received) / (1024 * 1024)
            self.data_label.config(text=f"{total_mb:.2f} MB")
        
        self.root.after(1000, self.update_stats)
    
    def update_ip(self):
        """Update current IP address"""
        thread = threading.Thread(target=self._update_ip_thread, daemon=True)
        thread.start()
    
    def _update_ip_thread(self):
        """Update IP in thread"""
        try:
            response = self.session.get("https://api.ipify.org?format=json", timeout=5)
            ip = response.json()['ip']
            self.root.after(0, lambda: self.ip_label.config(text=ip))
            self.current_ip = ip
        except:
            pass
    
    def browse_config(self):
        """Browse for config file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select VPN Config File",
            filetypes=[("OpenVPN Config", "*.ovpn"), ("All Files", "*.*")]
        )
        if filename:
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, filename)
            self.config_path = filename
    
    def save_settings(self):
        """Save settings"""
        self.username = self.username_entry.get()
        self.config_path = self.config_entry.get()
        
        config = {
            'username': self.username,
            'config_path': str(self.config_path) if self.config_path else None,
            'auto_connect': self.auto_connect_var.get(),
            'kill_switch': self.kill_switch_var.get(),
            'vpn_mode': self.vpn_mode,
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        messagebox.showinfo("Settings Saved", "Settings have been saved!")
    
    def load_config(self):
        """Load saved configuration"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
                    self.username = config.get('username')
                    self.config_path = config.get('config_path')
                    self.vpn_mode = config.get('vpn_mode', 'normal')
            except:
                pass
    
    def log(self, message):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.insert(tk.END, log_msg)
        self.logs_text.see(tk.END)
        self.logs_text.config(state=tk.DISABLED)
        
        # Also write to file
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_msg)
        except:
            pass
    
    def process_queue(self):
        """Process update queue"""
        try:
            while True:
                func = self.update_queue.get_nowait()
                func()
        except:
            pass
        self.root.after(100, self.process_queue)
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == '__main__':
    app = PhazeVPNUnified()

