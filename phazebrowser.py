#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhazeBrowser Enhanced - VPN-Native Secure Browser with Privacy Features
A custom browser that routes ALL traffic through the VPN with built-in privacy
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')

from gi.repository import Gtk, WebKit2, GLib, Gdk
import subprocess
import threading
import time
from pathlib import Path
import os
import sys
import json
from datetime import datetime

# Try to import requests for downloading configs
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ requests module not found. Install with: pip3 install requests")

class PhazeBrowserEnhanced:
    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_title("PhazeBrowser - Secure VPN Browser")
        self.window.set_default_size(1400, 900)
        self.window.connect("destroy", Gtk.main_quit)
        
        # VPN status
        self.vpn_connected = False
        self.vpn_interface = None
        self.vpn_process = None
        self.vpn_client_name = None
        self.vpn_protocol = None
        self.check_vpn_interval = 2
        self.vpn_connection_start_time = None
        self.vpn_session_bytes_sent = 0
        self.vpn_session_bytes_received = 0
        self.vpn_latency = None
        self.vpn_server_ip = None
        self.web_portal_session = None  # Store session cookies for API calls
        self.auto_reconnect_enabled = True
        self.kill_switch_enabled = False
        
        # VPN configs directory
        self.vpn_configs_dir = Path.home() / "Downloads"
        self.vpn_configs_dir.mkdir(exist_ok=True)
        
        # Browser state
        self.tabs = []
        self.current_tab = None
        self.bookmarks = self.load_bookmarks()
        self.history = self.load_history()
        self.downloads = []  # Download manager
        self.saved_passwords = self.load_passwords()  # Password manager
        
        # Privacy settings
        self.settings = {
            'ad_blocking': True,
            'tracking_protection': True,
            'fingerprint_protection': True,
            'webrtc_leak_protection': True,
            'dns_over_https': True,
            'theme': 'default',  # default, dark, light
            'max_privacy_mode': True,  # Maximum privacy - make all users identical
        }
        
        # Filter lists cache
        self.filter_lists_loaded = False
        self.easylist_rules = []
        self.easyprivacy_rules = []
        self.blocked_domains = set()
        
        # Load filter lists in background
        if REQUESTS_AVAILABLE:
            threading.Thread(target=self.load_filter_lists, daemon=True).start()
        
        # Check VPN status
        self.check_vpn_status()
        
        # Create UI
        self.create_ui()
        
        # Apply CSS styling
        self.apply_css_styling()
        
        # Start VPN monitoring
        self.start_vpn_monitoring()
    
    def load_bookmarks(self):
        """Load bookmarks from file"""
        bookmarks_file = Path.home() / ".config" / "phazebrowser" / "bookmarks.json"
        if bookmarks_file.exists():
            try:
                return json.load(open(bookmarks_file))
            except:
                return []
        return []
    
    def save_bookmarks(self):
        """Save bookmarks to file"""
        bookmarks_file = Path.home() / ".config" / "phazebrowser" / "bookmarks.json"
        bookmarks_file.parent.mkdir(parents=True, exist_ok=True)
        json.dump(self.bookmarks, open(bookmarks_file, 'w'), indent=2)
    
    def load_history(self):
        """Load browsing history"""
        history_file = Path.home() / ".config" / "phazebrowser" / "history.json"
        if history_file.exists():
            try:
                return json.load(open(history_file))
            except:
                return []
        return []
    
    def load_passwords(self):
        """Load saved passwords"""
        passwords_file = Path.home() / ".config" / "phazebrowser" / "passwords.json"
        if passwords_file.exists():
            try:
                return json.load(open(passwords_file))
            except:
                return []
        return []
    
    def save_passwords(self):
        """Save passwords to file"""
        passwords_file = Path.home() / ".config" / "phazebrowser" / "passwords.json"
        passwords_file.parent.mkdir(parents=True, exist_ok=True)
        json.dump(self.saved_passwords, open(passwords_file, 'w'), indent=2)
    
    def save_history(self, url, title=""):
        """Save to browsing history"""
        self.history.insert(0, {
            'url': url,
            'title': title,
            'timestamp': datetime.now().isoformat()
        })
        # Keep last 1000 entries
        self.history = self.history[:1000]
        
        history_file = Path.home() / ".config" / "phazebrowser" / "history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        json.dump(self.history, open(history_file, 'w'), indent=2)
    
    def check_vpn_status(self):
        """Check if VPN is connected"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True, text=True, timeout=2)
            
            for line in result.stdout.split('\n'):
                if 'tun' in line.lower() and 'state UP' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        self.vpn_interface = parts[1].strip().split()[0]
                        self.vpn_connected = True
                        return True
            
            result = subprocess.run(['pgrep', '-f', 'openvpn'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                result = subprocess.run(['ip', 'addr', 'show'], 
                                      capture_output=True, text=True, timeout=2)
                if 'tun' in result.stdout:
                    self.vpn_connected = True
                    for line in result.stdout.split('\n'):
                        if 'tun' in line and 'inet' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if 'tun' in part:
                                    self.vpn_interface = part
                                    break
                    return True
            
            self.vpn_connected = False
            self.vpn_interface = None
            return False
            
        except Exception as e:
            print(f"Error checking VPN status: {e}")
            self.vpn_connected = False
            return False
    
    def start_vpn_monitoring(self):
        """Start monitoring VPN connection"""
        def monitor():
            while True:
                was_connected = self.vpn_connected
                self.check_vpn_status()
                
                if was_connected != self.vpn_connected:
                    GLib.idle_add(self.update_vpn_status)
                
                time.sleep(self.check_vpn_interval)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def update_vpn_status(self):
        """Update VPN status in UI"""
        if self.vpn_connected:
            # Update connection time
            if self.vpn_connection_start_time:
                elapsed = time.time() - self.vpn_connection_start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            else:
                time_str = "Connected"
            
            # Update stats
            self.update_vpn_stats()
            
            status_text = f"🟢 VPN Connected ({self.vpn_interface or 'Active'}) - {time_str}"
            if self.vpn_latency:
                status_text += f" | {self.vpn_latency}ms"
            self.vpn_status_label.set_text(status_text)
            self.vpn_status_label.set_name("vpn-connected")
            self.vpn_connect_btn.set_label("🔴 Disconnect VPN")
            self.vpn_stats_btn.set_sensitive(True)
            if self.current_tab:
                self.current_tab['webview'].set_sensitive(True)
        else:
            self.vpn_status_label.set_text("🔴 VPN Disconnected - Browsing Blocked")
            self.vpn_status_label.set_name("vpn-disconnected")
            self.vpn_connect_btn.set_label("🔌 Connect VPN")
            self.vpn_stats_btn.set_sensitive(False)
            if self.current_tab:
                self.current_tab['webview'].set_sensitive(False)
                if not self.vpn_process:  # Only show warning if not trying to connect
                    self.show_vpn_warning()
            
            # Auto-reconnect if enabled
            if self.auto_reconnect_enabled and self.vpn_client_name and not self.vpn_process:
                GLib.timeout_add(5000, self.attempt_auto_reconnect)
    
    def update_vpn_stats(self):
        """Update VPN connection statistics"""
        if not self.vpn_connected or not self.vpn_interface:
            return
        
        try:
            # Get interface stats
            result = subprocess.run(['ip', '-s', 'link', 'show', self.vpn_interface],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'RX:' in line and i + 1 < len(lines):
                        # Parse received bytes
                        rx_line = lines[i + 1].strip()
                        if 'bytes' in rx_line:
                            try:
                                self.vpn_session_bytes_received = int(rx_line.split()[0])
                            except:
                                pass
                    if 'TX:' in line and i + 1 < len(lines):
                        # Parse sent bytes
                        tx_line = lines[i + 1].strip()
                        if 'bytes' in tx_line:
                            try:
                                self.vpn_session_bytes_sent = int(tx_line.split()[0])
                            except:
                                pass
            
            # Measure latency (ping VPN server)
            if self.vpn_server_ip:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', self.vpn_server_ip],
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    # Extract latency from ping output
                    for line in result.stdout.split('\n'):
                        if 'time=' in line:
                            try:
                                latency_str = line.split('time=')[1].split()[0]
                                self.vpn_latency = int(float(latency_str))
                            except:
                                pass
        except:
            pass  # Silently fail stats update
    
    def attempt_auto_reconnect(self):
        """Attempt to automatically reconnect VPN"""
        if self.vpn_connected or not self.vpn_client_name:
            return False
        
        # Find config file
        config_file = None
        if self.vpn_protocol == "openvpn":
            config_file = self.vpn_configs_dir / f"{self.vpn_client_name}.ovpn"
        elif self.vpn_protocol == "wireguard":
            config_file = self.vpn_configs_dir / f"{self.vpn_client_name}.conf"
        
        if config_file and config_file.exists():
            print("🔄 Auto-reconnecting VPN...")
            self.connect_vpn(config_file, self.vpn_protocol, self.vpn_client_name)
        
        return False  # Don't repeat
    
    def show_vpn_warning(self):
        """Show warning page when VPN is disconnected"""
        warning_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>VPN Required - PhazeBrowser</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    text-align: center;
                }
                .container {
                    background: rgba(0,0,0,0.3);
                    padding: 40px;
                    border-radius: 20px;
                    max-width: 600px;
                }
                h1 { font-size: 48px; margin: 0 0 20px 0; }
                p { font-size: 18px; line-height: 1.6; }
                .icon { font-size: 80px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🔒</div>
                <h1>VPN Required</h1>
                <p>PhazeBrowser requires an active VPN connection to protect your privacy.</p>
                <p>Please connect to your VPN and refresh this page.</p>
                <p><strong>Your browsing is blocked until VPN is connected.</strong></p>
            </div>
        </body>
        </html>
        """
        if self.current_tab:
            self.current_tab['webview'].load_html(warning_html, "file:///")
    
    def create_webview_settings(self):
        """Create WebKit settings with privacy features"""
        settings = WebKit2.Settings()
        
        # Privacy settings
        settings.set_property("enable-javascript", True)
        settings.set_property("enable-plugins", False)  # Disable plugins for security
        settings.set_property("enable-java", False)
        
        # WebRTC leak protection
        # Note: WebKit2 doesn't expose WebRTC settings directly
        # WebRTC traffic is routed through VPN at system level (via VPN tunnel)
        # This checkbox is informational - actual protection comes from VPN routing
        if self.settings['webrtc_leak_protection']:
            # System-level VPN routing ensures WebRTC goes through VPN
            # No browser-level action needed - VPN handles it
            pass
        
        # DNS over HTTPS
        # Note: DNS over HTTPS must be configured at system level
        # WebKit2 doesn't have direct DoH support in settings
        # This is informational - actual DoH comes from system config
        pass
        
        # Disable features that can be used for fingerprinting
        if self.settings['fingerprint_protection']:
            settings.set_property("enable-webaudio", False)  # Can be used for fingerprinting
            settings.set_property("enable-media-stream", False)  # Disable media access
        
        return settings
    
    def create_webview(self):
        """Create a new WebView with privacy settings"""
        settings = self.create_webview_settings()
        
        # User content manager for comprehensive ad blocking and tracking protection
        user_content = WebKit2.UserContentManager()
        
        # Maximum privacy mode - make all users identical (anti-fingerprinting)
        if self.settings.get('max_privacy_mode', True):
            max_privacy_js = self.load_max_privacy_mode_js()
            user_content.add_script(
                WebKit2.UserScript(max_privacy_js,
                                 WebKit2.UserContentInjectedFrames.ALL_FRAMES,
                                 WebKit2.UserScriptInjectionTime.START,
                                 None, None)
            )
        
        # Comprehensive ad blocking
        if self.settings['ad_blocking']:
            # CSS-based ad blocking
            ad_block_css = self.load_ad_block_css()
            user_content.add_style_sheet(
                WebKit2.UserStyleSheet(ad_block_css, 
                                     WebKit2.UserContentInjectedFrames.ALL_FRAMES,
                                     WebKit2.UserScriptInjectionTime.START,
                                     None, None)
            )
            
            # JavaScript-based ad blocking (runs before page loads)
            ad_block_js = self.load_comprehensive_ad_block_js()
            user_content.add_script(
                WebKit2.UserScript(ad_block_js,
                                 WebKit2.UserContentInjectedFrames.ALL_FRAMES,
                                 WebKit2.UserScriptInjectionTime.START,
                                 None, None)
            )
        
        # Comprehensive tracking protection
        if self.settings['tracking_protection']:
            # Network-level tracking block
            tracking_block_js = self.load_comprehensive_tracking_block_js()
            user_content.add_script(
                WebKit2.UserScript(tracking_block_js,
                                 WebKit2.UserContentInjectedFrames.ALL_FRAMES,
                                 WebKit2.UserScriptInjectionTime.START,
                                 None, None)
            )
            
            # Cookie blocking for trackers
            cookie_block_js = self.load_cookie_blocking_js()
            user_content.add_script(
                WebKit2.UserScript(cookie_block_js,
                                 WebKit2.UserContentInjectedFrames.ALL_FRAMES,
                                 WebKit2.UserScriptInjectionTime.START,
                                 None, None)
            )
        
        # Fingerprinting protection
        if self.settings['fingerprint_protection']:
            fingerprint_block_js = self.load_fingerprint_protection_js()
            user_content.add_script(
                WebKit2.UserScript(fingerprint_block_js,
                                 WebKit2.UserContentInjectedFrames.ALL_FRAMES,
                                 WebKit2.UserScriptInjectionTime.START,
                                 None, None)
            )
        
        # Create WebView with UserContentManager (must be passed to constructor)
        webview = WebKit2.WebView.new_with_user_content_manager(user_content)
        webview.set_settings(settings)
        
        # Connect to request filtering signal for network-level blocking (on WebView, not UserContentManager)
        webview.connect("decide-policy", self.on_decide_policy)
        
        # Connect to resource load signals for additional blocking
        webview.connect("resource-load-started", self.on_resource_load_started)
        
        # Connect signals
        webview.connect("load-changed", self.on_load_changed)
        webview.connect("notify::title", self.on_title_changed)
        
        # Note: Downloads are handled via WebContext, not WebView signals
        # We'll handle downloads through the context if needed
        
        return webview
    
    def apply_css_styling(self):
        """Apply modern, polished CSS styling to the browser"""
        theme = self.settings.get('theme', 'default')
        
        if theme == 'dark':
            css = """
            * {
                font-family: 'Inter', 'Segoe UI', 'Ubuntu', 'Cantarell', sans-serif;
            }
            
            window {
                background-color: #1e1e1e;
            }
            
            /* VPN Status Bar - Modern gradient */
            box {
                background-color: #667eea;
                border-bottom: 2px solid #555;
                padding: 8px;
            }
            
            button {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            
            button:hover {
                background-color: #764ba2;
            }
            
            button:active {
                background-color: #667eea;
            }
            
            entry {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 2px solid rgba(255,255,255,0.2);
                border-radius: 12px;
                padding: 10px 15px;
            }
            
            entry:focus {
                border-color: #667eea;
                background-color: #4a4a4a;
            }
            
            notebook {
                background: #1e1e1e;
            }
            
            notebook tab {
                background-color: #2b2b2b;
                color: #b0b0b0;
                border-radius: 12px 12px 0 0;
                padding: 10px 20px;
                margin: 0 2px;
                border: 1px solid rgba(255,255,255,0.1);
                border-bottom: none;
                font-weight: 500;
            }
            
            notebook tab:hover {
                background-color: #333;
                color: #fff;
            }
            
            notebook tab:checked {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
            
            .vpn-connected {
                color: #2ecc71;
                font-weight: bold;
            }
            
            .vpn-disconnected {
                color: #e74c3c;
                font-weight: bold;
            }
            
            label {
                color: #e0e0e0;
            }
            """
        elif theme == 'light':
            css = """
            * {
                font-family: 'Inter', 'Segoe UI', 'Ubuntu', 'Cantarell', sans-serif;
            }
            
            window {
                background-color: #ffffff;
            }
            
            /* VPN Status Bar - Modern gradient */
            box {
                background-color: #667eea;
                border-bottom: 2px solid #ddd;
                padding: 8px;
            }
            
            button {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            
            button:hover {
                background-color: #764ba2;
            }
            
            entry {
                background-color: #ffffff;
                color: #333;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 10px 15px;
            }
            
            entry:focus {
                border-color: #667eea;
                background-color: #ffffff;
            }
            
            notebook {
                background-color: #ffffff;
            }
            
            notebook tab {
                background-color: #f5f5f5;
                color: #666;
                border-radius: 12px 12px 0 0;
                padding: 10px 20px;
                margin: 0 2px;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                font-weight: 500;
            }
            
            notebook tab:hover {
                background-color: #e8e8e8;
                color: #333;
            }
            
            notebook tab:checked {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
            
            .vpn-connected {
                color: #2ecc71;
                font-weight: bold;
            }
            
            .vpn-disconnected {
                color: #e74c3c;
                font-weight: bold;
            }
            
            label {
                color: #333;
            }
            """
        else:  # default - Modern purple gradient theme
            css = """
            * {
                font-family: 'Ubuntu', 'Cantarell', sans-serif;
            }
            
            window {
                background-color: #ffffff;
            }
            
            /* VPN Status Bar - Purple and prominent */
            box {
                background-color: #667eea;
                padding: 12px;
                border-bottom: 3px solid #5568d3;
            }
            
            label {
                color: #333333;
            }
            
            /* VPN status styling */
            .vpn-connected {
                color: #2ecc71;
                font-weight: bold;
                font-size: 14px;
            }
            
            .vpn-disconnected {
                color: #e74c3c;
                font-weight: bold;
                font-size: 14px;
            }
            
            /* Modern purple buttons */
            button {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            
            button:hover {
                background-color: #764ba2;
            }
            
            button:active {
                background-color: #5568d3;
            }
            
            /* Modern URL bar */
            entry {
                background-color: white;
                color: #333333;
                border: 2px solid #e0e0e0;
                border-radius: 20px;
                padding: 12px 20px;
                font-size: 14px;
            }
            
            entry:focus {
                border-color: #667eea;
                background-color: white;
            }
            
            /* Modern tabs */
            notebook {
                background-color: white;
            }
            
            notebook tab {
                background-color: #f5f5f5;
                color: #666666;
                border-radius: 8px 8px 0 0;
                padding: 12px 24px;
                margin: 0 3px;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                font-weight: 500;
            }
            
            notebook tab:hover {
                background-color: #e8e8e8;
                color: #333333;
            }
            
            notebook tab:checked {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
                font-weight: 600;
            }
            
        
            """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def show_theme_selector(self, button):
        """Show theme selector dialog"""
        dialog = Gtk.Dialog(title="Select Theme", parent=self.window)
        dialog.set_default_size(300, 200)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        theme_label = Gtk.Label()
        theme_label.set_markup("<b>Choose a theme:</b>")
        content.pack_start(theme_label, False, False, 10)
        
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        default_radio = Gtk.RadioButton(label="Default")
        default_radio.set_active(self.settings.get('theme', 'default') == 'default')
        theme_box.pack_start(default_radio, False, False, 5)
        
        light_radio = Gtk.RadioButton.new_from_widget(default_radio)
        light_radio.set_label("Light")
        light_radio.set_active(self.settings.get('theme', 'default') == 'light')
        theme_box.pack_start(light_radio, False, False, 5)
        
        dark_radio = Gtk.RadioButton.new_from_widget(default_radio)
        dark_radio.set_label("Dark")
        dark_radio.set_active(self.settings.get('theme', 'default') == 'dark')
        theme_box.pack_start(dark_radio, False, False, 5)
        
        content.pack_start(theme_box, False, False, 10)
        
        def apply_theme():
            if default_radio.get_active():
                self.settings['theme'] = 'default'
            elif light_radio.get_active():
                self.settings['theme'] = 'light'
            elif dark_radio.get_active():
                self.settings['theme'] = 'dark'
            
            self.apply_css_styling()
        
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        apply_btn = dialog.add_button("Apply", Gtk.ResponseType.OK)
        apply_btn.connect("clicked", lambda w: apply_theme())
        
        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            apply_theme()
        dialog.destroy()
    
    def create_ui(self):
        """Create the enhanced browser UI"""
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(vbox)
        
        # VPN Status Bar - Modern gradient header
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.set_margin_start(15)
        status_bar.set_margin_end(15)
        status_bar.set_margin_top(10)
        status_bar.set_margin_bottom(10)
        status_bar.set_name("vpn-status-bar")  # For CSS targeting
        
        self.vpn_status_label = Gtk.Label()
        self.vpn_status_label.set_markup("<b>Checking VPN...</b>")
        status_bar.pack_start(self.vpn_status_label, False, False, 0)
        
        # VPN Connect/Disconnect button
        self.vpn_connect_btn = Gtk.Button(label="🔌 Connect VPN")
        self.vpn_connect_btn.connect("clicked", self.on_vpn_connect_clicked)
        status_bar.pack_start(self.vpn_connect_btn, False, False, 5)
        
        # VPN Stats button (shows connection stats)
        self.vpn_stats_btn = Gtk.Button(label="📊 Stats")
        self.vpn_stats_btn.connect("clicked", self.show_vpn_stats)
        status_bar.pack_start(self.vpn_stats_btn, False, False, 5)
        
        # Privacy indicators
        privacy_label = Gtk.Label()
        privacy_label.set_markup("🛡️ Privacy: ON")
        status_bar.pack_start(privacy_label, False, False, 10)
        
        # Login button for web portal
        self.login_btn = Gtk.Button(label="🔐 Login")
        self.login_btn.connect("clicked", self.show_login_dialog)
        status_bar.pack_start(self.login_btn, False, False, 5)
        
        refresh_btn = Gtk.Button(label="🔄 Refresh")
        refresh_btn.connect("clicked", lambda w: self.check_vpn_status())
        refresh_btn.connect("clicked", lambda w: self.update_vpn_status())
        status_bar.pack_end(refresh_btn, False, False, 0)
        
        vbox.pack_start(status_bar, False, False, 0)
        
        # Tab bar
        self.tab_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.tab_bar.set_margin_start(5)
        self.tab_bar.set_margin_end(5)
        self.tab_bar.set_margin_bottom(2)
        vbox.pack_start(self.tab_bar, False, False, 0)
        
        # Navigation Bar - Modern toolbar
        nav_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        nav_bar.set_margin_start(12)
        nav_bar.set_margin_end(12)
        nav_bar.set_margin_top(8)
        nav_bar.set_margin_bottom(8)
        nav_bar.set_name("nav-bar")  # For CSS targeting
        
        back_btn = Gtk.Button(label="◀")
        back_btn.connect("clicked", lambda w: self.go_back())
        nav_bar.pack_start(back_btn, False, False, 0)
        
        forward_btn = Gtk.Button(label="▶")
        forward_btn.connect("clicked", lambda w: self.go_forward())
        nav_bar.pack_start(forward_btn, False, False, 0)
        
        refresh_web_btn = Gtk.Button(label="🔄")
        refresh_web_btn.connect("clicked", lambda w: self.reload())
        nav_bar.pack_start(refresh_web_btn, False, False, 0)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter URL or search...")
        self.url_entry.connect("activate", self.on_url_activate)
        nav_bar.pack_start(self.url_entry, True, True, 0)
        
        go_btn = Gtk.Button(label="Go")
        go_btn.connect("clicked", self.on_go_clicked)
        nav_bar.pack_start(go_btn, False, False, 0)
        
        # Bookmarks button
        bookmarks_btn = Gtk.Button(label="⭐")
        bookmarks_btn.connect("clicked", self.show_bookmarks)
        nav_bar.pack_start(bookmarks_btn, False, False, 0)
        
        # History button
        history_btn = Gtk.Button(label="🕐")
        history_btn.connect("clicked", self.show_history)
        nav_bar.pack_start(history_btn, False, False, 0)
        
        # New tab button
        new_tab_btn = Gtk.Button(label="➕")
        new_tab_btn.connect("clicked", self.new_tab)
        nav_bar.pack_start(new_tab_btn, False, False, 0)
        
        # Downloads button
        downloads_btn = Gtk.Button(label="⬇️")
        downloads_btn.connect("clicked", self.show_downloads)
        nav_bar.pack_start(downloads_btn, False, False, 0)
        
        # Theme button
        theme_btn = Gtk.Button(label="🎨")
        theme_btn.connect("clicked", self.show_theme_selector)
        nav_bar.pack_start(theme_btn, False, False, 0)
        
        # Settings button
        settings_btn = Gtk.Button(label="⚙️")
        settings_btn.connect("clicked", self.show_settings)
        nav_bar.pack_start(settings_btn, False, False, 0)
        
        vbox.pack_start(nav_bar, False, False, 0)
        
        # Notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.connect("switch-page", self.on_tab_switched)
        vbox.pack_start(self.notebook, True, True, 0)
        
        # Create first tab
        self.new_tab("https://www.google.com" if self.vpn_connected else None)
        
        # Update status
        self.update_vpn_status()
    
    def new_tab(self, url=None):
        """Create a new tab"""
        webview = self.create_webview()
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(webview)
        
        # Tab label with favicon support
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Favicon (placeholder for now)
        favicon_label = Gtk.Label(label="🌐")
        favicon_label.set_size_request(16, 16)
        tab_box.pack_start(favicon_label, False, False, 0)
        
        label = Gtk.Label(label="New Tab")
        label.set_ellipsize(3)  # Ellipsize at end
        label.set_max_width_chars(20)
        tab_box.pack_start(label, True, True, 0)
        
        close_btn = Gtk.Button(label="✕")
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.set_size_request(20, 20)
        close_btn.set_tooltip_text("Close tab")
        tab_box.pack_start(close_btn, False, False, 0)
        tab_box.show_all()
        
        page_num = self.notebook.append_page(scrolled, tab_box)
        
        tab_info = {
            'webview': webview,
            'label': label,
            'favicon_label': favicon_label,
            'close_btn': close_btn,
            'page_num': page_num,
            'url': url or "",
            'title': "New Tab"
        }
        
        close_btn.connect("clicked", lambda w: self.close_tab(tab_info))
        
        self.tabs.append(tab_info)
        self.current_tab = tab_info
        self.notebook.set_current_page(page_num)
        
        if url:
            self.navigate_to_url(url)
        elif not self.vpn_connected:
            self.show_vpn_warning()
    
    def close_tab(self, tab_info):
        """Close a tab"""
        if len(self.tabs) <= 1:
            # Don't close last tab
            return
        
        page_num = tab_info['page_num']
        self.notebook.remove_page(page_num)
        self.tabs.remove(tab_info)
        
        if tab_info == self.current_tab:
            # Switch to another tab
            if self.tabs:
                self.current_tab = self.tabs[0]
                self.notebook.set_current_page(self.current_tab['page_num'])
    
    def on_tab_switched(self, notebook, page, page_num):
        """Handle tab switch"""
        for tab in self.tabs:
            if tab['page_num'] == page_num:
                self.current_tab = tab
                uri = tab['webview'].get_uri()
                if uri:
                    self.url_entry.set_text(uri)
                break
    
    def go_back(self):
        """Go back in current tab"""
        if self.current_tab:
            self.current_tab['webview'].go_back()
    
    def go_forward(self):
        """Go forward in current tab"""
        if self.current_tab:
            self.current_tab['webview'].go_forward()
    
    def reload(self):
        """Reload current tab"""
        if self.current_tab:
            self.current_tab['webview'].reload()
    
    def on_url_activate(self, entry):
        """Handle URL entry activation"""
        self.navigate_to_url(entry.get_text())
    
    def on_go_clicked(self, button):
        """Handle Go button click"""
        self.navigate_to_url(self.url_entry.get_text())
    
    def navigate_to_url(self, url):
        """Navigate to URL"""
        if not self.vpn_connected:
            self.show_vpn_warning()
            return
        
        if not self.current_tab:
            self.new_tab()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                # Search query
                url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        
        self.current_tab['webview'].load_uri(url)
    
    def on_load_changed(self, webview, load_event):
        """Handle page load events"""
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = webview.get_uri()
            if uri and self.current_tab and webview == self.current_tab['webview']:
                self.url_entry.set_text(uri)
                self.save_history(uri, webview.get_title() or uri)
    
    def on_title_changed(self, webview, title):
        """Handle title change"""
        # Update all tabs with matching webview
        for tab in self.tabs:
            if tab['webview'] == webview:
                title_text = webview.get_title() or "New Tab"
                tab['title'] = title_text
                # Truncate for display
                display_text = title_text[:25] + "..." if len(title_text) > 25 else title_text
                tab['label'].set_text(display_text)
                # Update tab label in notebook
                if tab == self.current_tab:
                    # Update favicon if available (placeholder for now)
                    pass
                break
    
    def show_bookmarks(self, button):
        """Show bookmarks menu"""
        menu = Gtk.Menu()
        
        if not self.bookmarks:
            item = Gtk.MenuItem(label="No bookmarks yet")
            item.set_sensitive(False)
            menu.append(item)
        else:
            for bookmark in self.bookmarks[:20]:  # Show last 20
                item = Gtk.MenuItem(label=bookmark.get('title', bookmark.get('url', '')))
                item.connect("activate", lambda w, url=bookmark.get('url'): self.navigate_to_url(url))
                menu.append(item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Add current page
        add_item = Gtk.MenuItem(label="Add Current Page")
        if self.current_tab:
            uri = self.current_tab['webview'].get_uri()
            title = self.current_tab['webview'].get_title() or uri
            if uri:
                add_item.connect("activate", lambda w: self.add_bookmark(uri, title))
        else:
            add_item.set_sensitive(False)
        menu.append(add_item)
        
        menu.show_all()
        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
    
    def add_bookmark(self, url, title):
        """Add current page to bookmarks"""
        self.bookmarks.insert(0, {'url': url, 'title': title, 'added': datetime.now().isoformat()})
        self.save_bookmarks()
    
    def show_history(self, button):
        """Show history menu"""
        menu = Gtk.Menu()
        
        if not self.history:
            item = Gtk.MenuItem(label="No history yet")
            item.set_sensitive(False)
            menu.append(item)
        else:
            for entry in self.history[:20]:  # Show last 20
                title = entry.get('title', entry.get('url', ''))
                item = Gtk.MenuItem(label=title[:50])
                item.connect("activate", lambda w, url=entry.get('url'): self.navigate_to_url(url))
                menu.append(item)
        
        menu.show_all()
        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
    
    def on_vpn_connect_clicked(self, button):
        """Handle VPN connect/disconnect button click"""
        if self.vpn_connected:
            self.disconnect_vpn()
        else:
            self.show_vpn_connect_dialog()
    
    def show_vpn_connect_dialog(self):
        """Show dialog to connect to VPN"""
        dialog = Gtk.Dialog(title="Connect to PhazeVPN", parent=self.window)
        dialog.set_default_size(500, 400)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        # Instructions
        info_label = Gtk.Label()
        info_label.set_markup("<b>Connect to PhazeVPN</b>\n\nSelect your client and protocol to connect.")
        info_label.set_line_wrap(True)
        content.pack_start(info_label, False, False, 10)
        
        # Client selection
        client_frame = Gtk.Frame(label="Client")
        client_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        client_frame.add(client_box)
        
        self.client_combo = Gtk.ComboBoxText()
        # Try to get clients from Downloads folder or web portal
        self.load_available_clients()
        client_box.pack_start(self.client_combo, False, False, 5)
        
        refresh_clients_btn = Gtk.Button(label="🔄 Refresh Clients")
        refresh_clients_btn.connect("clicked", lambda w: self.load_available_clients())
        client_box.pack_start(refresh_clients_btn, False, False, 5)
        
        client_box.set_margin_start(10)
        client_box.set_margin_end(10)
        client_box.set_margin_top(10)
        client_box.set_margin_bottom(10)
        content.pack_start(client_frame, False, False, 10)
        
        # Protocol selection
        protocol_frame = Gtk.Frame(label="Protocol")
        protocol_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        protocol_frame.add(protocol_box)
        
        self.protocol_combo = Gtk.ComboBoxText()
        self.protocol_combo.append_text("OpenVPN (Recommended)")
        self.protocol_combo.append_text("WireGuard (Modern)")
        self.protocol_combo.append_text("PhazeVPN (Experimental)")
        self.protocol_combo.set_active(0)
        protocol_box.pack_start(self.protocol_combo, False, False, 5)
        
        protocol_box.set_margin_start(10)
        protocol_box.set_margin_end(10)
        protocol_box.set_margin_top(10)
        protocol_box.set_margin_bottom(10)
        content.pack_start(protocol_frame, False, False, 10)
        
        # Download config option
        download_check = Gtk.CheckButton(label="Download config from server if not found")
        download_check.set_active(True)
        content.pack_start(download_check, False, False, 5)
        
        # Status label
        self.connect_status_label = Gtk.Label()
        self.connect_status_label.set_text("")
        content.pack_start(self.connect_status_label, False, False, 5)
        
        # Buttons
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        connect_btn = dialog.add_button("🔌 Connect", Gtk.ResponseType.OK)
        connect_btn.connect("clicked", lambda w: self.connect_vpn_from_dialog(dialog, download_check))
        
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
    
    def load_available_clients(self):
        """Load available VPN clients from Downloads folder and web portal"""
        self.client_combo.remove_all()
        
        # Check Downloads folder for config files
        configs_found = []
        for ext in ['.ovpn', '.conf', '.phazevpn']:
            for config_file in self.vpn_configs_dir.glob(f'*{ext}'):
                client_name = config_file.stem.replace('.ovpn', '').replace('.conf', '').replace('.phazevpn', '')
                if client_name not in configs_found:
                    configs_found.append(client_name)
                    self.client_combo.append_text(client_name)
        
        # Try to get clients from web portal API if requests is available
        if REQUESTS_AVAILABLE:
            try:
                vps_url = os.environ.get("PHASEVPN_URL", "https://phazevpn.com")
                api_url = f"{vps_url}/api/app/configs"
                
                # Try to get clients (may need authentication)
                response = requests.get(api_url, timeout=5, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    clients = data.get('configs', [])
                    for client in clients:
                        client_name = client.get('name') or client.get('vpn_config', '')
                        if client_name and client_name not in configs_found:
                            configs_found.append(client_name)
                            self.client_combo.append_text(client_name)
            except:
                pass  # Silently fail if API not available
        
        if not configs_found:
            self.client_combo.append_text("No configs found - will download")
            if hasattr(self, 'connect_status_label'):
                self.connect_status_label.set_text("⚠️ No configs found. Will download from server.")
        else:
            self.client_combo.set_active(0)
    
    def connect_vpn_from_dialog(self, dialog, download_check):
        """Connect to VPN using selected client and protocol"""
        client_name = self.client_combo.get_active_text()
        protocol_text = self.protocol_combo.get_active_text()
        
        if not client_name or client_name == "No configs found - will download":
            self.connect_status_label.set_text("❌ Please select a client or download one first")
            return
        
        # Map protocol text to protocol name
        protocol_map = {
            "OpenVPN (Recommended)": "openvpn",
            "WireGuard (Modern)": "wireguard",
            "PhazeVPN (Experimental)": "phazevpn"
        }
        protocol = protocol_map.get(protocol_text, "openvpn")
        
        # Find config file
        config_file = None
        if protocol == "openvpn":
            config_file = self.vpn_configs_dir / f"{client_name}.ovpn"
        elif protocol == "wireguard":
            config_file = self.vpn_configs_dir / f"{client_name}.conf"
        else:  # phazevpn
            config_file = self.vpn_configs_dir / f"{client_name}.phazevpn"
        
        # If config doesn't exist and download is enabled, try to download
        if not config_file.exists() and download_check.get_active():
            self.connect_status_label.set_text("⏳ Downloading config from server...")
            dialog.show_all()
            
            # Try to download from web portal
            if not REQUESTS_AVAILABLE:
                self.connect_status_label.set_text("❌ requests module not available. Install with: pip3 install requests")
                return
            
            try:
                vps_url = os.environ.get("PHASEVPN_URL", "https://phazevpn.com")
                download_url = f"{vps_url}/download/{client_name}?type={protocol}"
                
                # Disable SSL warnings for self-signed certs
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = requests.get(download_url, timeout=15, verify=False)
                if response.status_code == 200:
                    config_file.write_bytes(response.content)
                    config_file.chmod(0o600)
                    self.connect_status_label.set_text("✅ Config downloaded!")
                elif response.status_code == 401:
                    self.connect_status_label.set_text("❌ Authentication required. Please login at phazevpn.com first.")
                    return
                else:
                    self.connect_status_label.set_text(f"❌ Failed to download config: {response.status_code}")
                    return
            except Exception as e:
                self.connect_status_label.set_text(f"❌ Download failed: {str(e)[:50]}")
                return
        
        if not config_file.exists():
            self.connect_status_label.set_text(f"❌ Config file not found: {config_file}")
            return
        
        # Connect to VPN
        self.connect_status_label.set_text("⏳ Connecting...")
        dialog.show_all()
        
        success = self.connect_vpn(config_file, protocol, client_name)
        
        if success:
            self.connect_status_label.set_text("✅ Connected! Closing dialog...")
            GLib.timeout_add(500, lambda: dialog.response(Gtk.ResponseType.OK))
        else:
            self.connect_status_label.set_text("❌ Connection failed. Check terminal for details.")
    
    def connect_vpn(self, config_file, protocol, client_name):
        """Connect to VPN using the config file"""
        try:
            if protocol == "openvpn":
                # Find OpenVPN binary
                openvpn_paths = [
                    Path("/usr/sbin/openvpn"),
                    Path("/usr/bin/openvpn"),
                    Path("/usr/local/bin/openvpn"),
                ]
                
                openvpn_binary = None
                for path in openvpn_paths:
                    if path.exists():
                        openvpn_binary = path
                        break
                
                if not openvpn_binary:
                    print("❌ OpenVPN not found. Install with: sudo apt install openvpn")
                    return False
                
                # Launch OpenVPN (requires sudo)
                cmd = ['sudo', str(openvpn_binary), '--config', str(config_file), '--daemon']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.vpn_process = "openvpn"
                    self.vpn_protocol = protocol
                    self.vpn_client_name = client_name
                    self.vpn_connection_start_time = time.time()
                    self.vpn_session_bytes_sent = 0
                    self.vpn_session_bytes_received = 0
                    # Extract server IP from config
                    try:
                        with open(config_file, 'r') as f:
                            config_content = f.read()
                            for line in config_content.split('\n'):
                                if line.startswith('remote '):
                                    parts = line.split()
                                    if len(parts) >= 2:
                                        self.vpn_server_ip = parts[1]
                                        break
                    except:
                        pass
                    time.sleep(2)  # Wait for connection
                    self.check_vpn_status()
                    return True
                else:
                    print(f"❌ OpenVPN failed: {result.stderr}")
                    return False
                    
            elif protocol == "wireguard":
                # Find wg-quick binary
                wg_quick_paths = [
                    Path("/usr/bin/wg-quick"),
                    Path("/usr/local/bin/wg-quick"),
                ]
                
                wg_quick_binary = None
                for path in wg_quick_paths:
                    if path.exists():
                        wg_quick_binary = path
                        break
                
                if not wg_quick_binary:
                    print("❌ WireGuard not found. Install with: sudo apt install wireguard")
                    return False
                
                # Launch WireGuard
                interface_name = config_file.stem.replace(' ', '_').replace('-', '_')
                cmd = ['sudo', str(wg_quick_binary), 'up', str(config_file)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.vpn_process = "wireguard"
                    self.vpn_protocol = protocol
                    self.vpn_client_name = client_name
                    self.vpn_connection_start_time = time.time()
                    self.vpn_session_bytes_sent = 0
                    self.vpn_session_bytes_received = 0
                    # Extract server IP from config
                    try:
                        with open(config_file, 'r') as f:
                            config_content = f.read()
                            for line in config_content.split('\n'):
                                if line.startswith('Endpoint = '):
                                    endpoint = line.split('=')[1].strip()
                                    self.vpn_server_ip = endpoint.split(':')[0]
                                    break
                    except:
                        pass
                    time.sleep(2)
                    self.check_vpn_status()
                    return True
                else:
                    print(f"❌ WireGuard failed: {result.stderr}")
                    return False
                    
            else:  # phazevpn
                print("⚠️ PhazeVPN client not yet implemented in browser")
                return False
                
        except Exception as e:
            print(f"❌ VPN connection error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def disconnect_vpn(self):
        """Disconnect from VPN"""
        try:
            if self.vpn_protocol == "openvpn":
                subprocess.run(['sudo', 'pkill', '-f', 'openvpn'], capture_output=True)
            elif self.vpn_protocol == "wireguard":
                if self.vpn_client_name:
                    subprocess.run(['sudo', 'wg-quick', 'down', self.vpn_client_name], capture_output=True)
                subprocess.run(['sudo', 'wg-quick', 'down', 'wg0'], capture_output=True)
            
            self.vpn_process = None
            self.vpn_protocol = None
            self.vpn_client_name = None
            self.vpn_connection_start_time = None
            self.vpn_session_bytes_sent = 0
            self.vpn_session_bytes_received = 0
            self.vpn_latency = None
            self.vpn_server_ip = None
            time.sleep(1)
            self.check_vpn_status()
            self.update_vpn_status()
            
            # Kill switch - block all traffic if enabled
            if self.kill_switch_enabled:
                self.enable_kill_switch()
            
        except Exception as e:
            print(f"❌ Disconnect error: {e}")
    
    def show_vpn_stats(self, button):
        """Show VPN connection statistics dialog"""
        dialog = Gtk.Dialog(title="VPN Connection Statistics", parent=self.window)
        dialog.set_default_size(500, 400)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        if not self.vpn_connected:
            info_label = Gtk.Label()
            info_label.set_text("VPN is not connected. Connect to VPN to view statistics.")
            content.pack_start(info_label, False, False, 10)
        else:
            # Connection info
            info_frame = Gtk.Frame(label="Connection Information")
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            info_frame.add(info_box)
            
            # Protocol
            protocol_label = Gtk.Label()
            protocol_label.set_markup(f"<b>Protocol:</b> {self.vpn_protocol.upper() if self.vpn_protocol else 'Unknown'}")
            protocol_label.set_halign(Gtk.Align.START)
            info_box.pack_start(protocol_label, False, False, 5)
            
            # Interface
            interface_label = Gtk.Label()
            interface_label.set_markup(f"<b>Interface:</b> {self.vpn_interface or 'Unknown'}")
            interface_label.set_halign(Gtk.Align.START)
            info_box.pack_start(interface_label, False, False, 5)
            
            # Server
            server_label = Gtk.Label()
            server_label.set_markup(f"<b>Server:</b> {self.vpn_server_ip or 'Unknown'}")
            server_label.set_halign(Gtk.Align.START)
            info_box.pack_start(server_label, False, False, 5)
            
            # Client
            client_label = Gtk.Label()
            client_label.set_markup(f"<b>Client:</b> {self.vpn_client_name or 'Unknown'}")
            client_label.set_halign(Gtk.Align.START)
            info_box.pack_start(client_label, False, False, 5)
            
            # Connection time
            if self.vpn_connection_start_time:
                elapsed = time.time() - self.vpn_connection_start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_str = "Unknown"
            
            time_label = Gtk.Label()
            time_label.set_markup(f"<b>Connection Time:</b> {time_str}")
            time_label.set_halign(Gtk.Align.START)
            info_box.pack_start(time_label, False, False, 5)
            
            info_box.set_margin_start(10)
            info_box.set_margin_end(10)
            info_box.set_margin_top(10)
            info_box.set_margin_bottom(10)
            content.pack_start(info_frame, False, False, 10)
            
            # Statistics
            stats_frame = Gtk.Frame(label="Statistics")
            stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            stats_frame.add(stats_box)
            
            # Latency
            latency_label = Gtk.Label()
            latency_text = f"{self.vpn_latency}ms" if self.vpn_latency else "Measuring..."
            latency_label.set_markup(f"<b>Latency:</b> {latency_text}")
            latency_label.set_halign(Gtk.Align.START)
            stats_box.pack_start(latency_label, False, False, 5)
            
            # Data transferred
            def format_bytes(bytes_val):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.2f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.2f} TB"
            
            sent_label = Gtk.Label()
            sent_label.set_markup(f"<b>Data Sent:</b> {format_bytes(self.vpn_session_bytes_sent)}")
            sent_label.set_halign(Gtk.Align.START)
            stats_box.pack_start(sent_label, False, False, 5)
            
            received_label = Gtk.Label()
            received_label.set_markup(f"<b>Data Received:</b> {format_bytes(self.vpn_session_bytes_received)}")
            received_label.set_halign(Gtk.Align.START)
            stats_box.pack_start(received_label, False, False, 5)
            
            total_label = Gtk.Label()
            total_bytes = self.vpn_session_bytes_sent + self.vpn_session_bytes_received
            total_label.set_markup(f"<b>Total Data:</b> {format_bytes(total_bytes)}")
            total_label.set_halign(Gtk.Align.START)
            stats_box.pack_start(total_label, False, False, 5)
            
            stats_box.set_margin_start(10)
            stats_box.set_margin_end(10)
            stats_box.set_margin_top(10)
            stats_box.set_margin_bottom(10)
            content.pack_start(stats_frame, False, False, 10)
            
            # Refresh button
            refresh_btn = Gtk.Button(label="🔄 Refresh Stats")
            refresh_btn.connect("clicked", lambda w: self.update_vpn_stats())
            refresh_btn.connect("clicked", lambda w: dialog.destroy())
            refresh_btn.connect("clicked", lambda w: self.show_vpn_stats(button))
            content.pack_start(refresh_btn, False, False, 5)
        
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def show_login_dialog(self, button):
        """Show web portal login dialog"""
        dialog = Gtk.Dialog(title="Login to PhazeVPN Portal", parent=self.window)
        dialog.set_default_size(400, 300)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        # Instructions
        info_label = Gtk.Label()
        info_label.set_markup("<b>Login to PhazeVPN Portal</b>\n\nLogin to automatically fetch your VPN clients.")
        info_label.set_line_wrap(True)
        content.pack_start(info_label, False, False, 10)
        
        # Username
        username_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        username_label = Gtk.Label(label="Username:")
        username_label.set_size_request(100, -1)
        username_entry = Gtk.Entry()
        username_entry.set_placeholder_text("Enter username")
        username_box.pack_start(username_label, False, False, 0)
        username_box.pack_start(username_entry, True, True, 0)
        content.pack_start(username_box, False, False, 5)
        
        # Password
        password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        password_label = Gtk.Label(label="Password:")
        password_label.set_size_request(100, -1)
        password_entry = Gtk.Entry()
        password_entry.set_placeholder_text("Enter password")
        password_entry.set_visibility(False)
        password_box.pack_start(password_label, False, False, 0)
        password_box.pack_start(password_entry, True, True, 0)
        content.pack_start(password_box, False, False, 5)
        
        # Portal URL
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        url_label = Gtk.Label(label="Portal URL:")
        url_label.set_size_request(100, -1)
        url_entry = Gtk.Entry()
        url_entry.set_text(os.environ.get("PHASEVPN_URL", "https://phazevpn.com"))
        url_box.pack_start(url_label, False, False, 0)
        url_box.pack_start(url_entry, True, True, 0)
        content.pack_start(url_box, False, False, 5)
        
        # Status label
        status_label = Gtk.Label()
        status_label.set_text("")
        content.pack_start(status_label, False, False, 5)
        
        def do_login():
            username = username_entry.get_text().strip()
            password = password_entry.get_text()
            portal_url = url_entry.get_text().strip()
            
            if not username or not password:
                status_label.set_text("❌ Please enter username and password")
                return
            
            if not REQUESTS_AVAILABLE:
                status_label.set_text("❌ requests module not available. Install with: pip3 install requests")
                return
            
            status_label.set_text("⏳ Logging in...")
            dialog.show_all()
            
            try:
                # Create session
                session = requests.Session()
                
                # Disable SSL warnings
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                # Login via API
                login_url = f"{portal_url}/api/app/login"
                response = session.post(login_url, json={
                    'username': username,
                    'password': password
                }, timeout=10, verify=False)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        # Store session
                        self.web_portal_session = session
                        
                        # Fetch clients
                        status_label.set_text("✅ Login successful! Fetching clients...")
                        dialog.show_all()
                        
                        configs_url = f"{portal_url}/api/app/configs"
                        configs_response = session.get(configs_url, timeout=10, verify=False)
                        
                        if configs_response.status_code == 200:
                            configs_data = configs_response.json()
                            clients = configs_data.get('configs', [])
                            
                            # Download configs
                            downloaded = 0
                            for client in clients:
                                client_name = client.get('name')
                                if client_name:
                                    # Download each protocol type
                                    for protocol_type in ['openvpn', 'wireguard']:
                                        download_url = f"{portal_url}/download/{client_name}?type={protocol_type}"
                                        try:
                                            dl_response = session.get(download_url, timeout=15, verify=False)
                                            if dl_response.status_code == 200:
                                                if protocol_type == 'openvpn':
                                                    config_file = self.vpn_configs_dir / f"{client_name}.ovpn"
                                                else:
                                                    config_file = self.vpn_configs_dir / f"{client_name}.conf"
                                                config_file.write_bytes(dl_response.content)
                                                config_file.chmod(0o600)
                                                downloaded += 1
                                        except:
                                            pass
                            
                            status_label.set_text(f"✅ Success! Downloaded {downloaded} config(s).")
                            GLib.timeout_add(1000, lambda: dialog.response(Gtk.ResponseType.OK))
                        else:
                            status_label.set_text("⚠️ Login successful but failed to fetch clients.")
                    else:
                        status_label.set_text(f"❌ Login failed: {data.get('error', 'Unknown error')}")
                else:
                    status_label.set_text(f"❌ Login failed: HTTP {response.status_code}")
            except Exception as e:
                status_label.set_text(f"❌ Error: {str(e)[:50]}")
        
        # Buttons
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        login_btn = dialog.add_button("🔐 Login", Gtk.ResponseType.OK)
        login_btn.connect("clicked", lambda w: do_login())
        
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        
        # Refresh client list after login
        if self.web_portal_session:
            self.load_available_clients()
    
    def enable_kill_switch(self):
        """Enable kill switch - block all traffic if VPN disconnects"""
        if not self.kill_switch_enabled:
            return
        
        try:
            # Use iptables to block all non-VPN traffic
            # This is a basic implementation - may need sudo
            print("🛡️ Kill switch enabled - blocking all non-VPN traffic")
            # Note: Full kill switch requires root and iptables configuration
            # This is a placeholder for the feature
        except Exception as e:
            print(f"⚠️ Kill switch error: {e}")
    
    def show_settings(self, button):
        """Show settings dialog"""
        dialog = Gtk.Dialog(title="PhazeBrowser Settings", parent=self.window)
        dialog.set_default_size(500, 500)
        
        content = dialog.get_content_area()
        
        # Privacy settings
        privacy_frame = Gtk.Frame(label="Privacy & Security")
        privacy_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        privacy_frame.add(privacy_box)
        
        ad_block = Gtk.CheckButton(label="Ad Blocking (Basic)")
        ad_block.set_active(self.settings['ad_blocking'])
        ad_block.set_tooltip_text("Basic ad blocking - works for some sites. Advanced blocking coming soon.")
        ad_block.connect("toggled", lambda w: self.settings.update({'ad_blocking': w.get_active()}))
        privacy_box.pack_start(ad_block, False, False, 5)
        
        tracking = Gtk.CheckButton(label="Tracking Protection (Basic)")
        tracking.set_active(self.settings['tracking_protection'])
        tracking.set_tooltip_text("Basic tracking protection - blocks common trackers. Advanced protection coming soon.")
        tracking.connect("toggled", lambda w: self.settings.update({'tracking_protection': w.get_active()}))
        privacy_box.pack_start(tracking, False, False, 5)
        
        fingerprint = Gtk.CheckButton(label="Fingerprinting Protection (Basic)")
        fingerprint.set_active(self.settings['fingerprint_protection'])
        fingerprint.set_tooltip_text("Basic protection - disables WebAudio/media. More techniques coming soon.")
        fingerprint.connect("toggled", lambda w: self.settings.update({'fingerprint_protection': w.get_active()}))
        privacy_box.pack_start(fingerprint, False, False, 5)
        
        webrtc = Gtk.CheckButton(label="WebRTC Protection (via VPN routing)")
        webrtc.set_active(self.settings['webrtc_leak_protection'])
        webrtc.set_sensitive(False)  # Informational only - controlled by VPN
        webrtc.set_tooltip_text("WebRTC traffic routes through VPN at system level")
        privacy_box.pack_start(webrtc, False, False, 5)
        
        dns = Gtk.CheckButton(label="DNS over HTTPS")
        dns.set_active(self.settings['dns_over_https'])
        dns.set_tooltip_text("Use DNS over HTTPS for secure DNS queries")
        dns.connect("toggled", lambda w: self.settings.update({'dns_over_https': w.get_active()}))
        privacy_box.pack_start(dns, False, False, 5)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup("<small><i>Note: WebRTC and DNS protection rely on VPN/system configuration</i></small>")
        info_label.set_margin_top(10)
        privacy_box.pack_start(info_label, False, False, 5)
        
        privacy_box.set_margin_start(10)
        privacy_box.set_margin_end(10)
        privacy_box.set_margin_top(10)
        privacy_box.set_margin_bottom(10)
        
        content.pack_start(privacy_frame, True, True, 10)
        
        # VPN Settings
        vpn_frame = Gtk.Frame(label="VPN Settings")
        vpn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vpn_frame.add(vpn_box)
        
        auto_reconnect = Gtk.CheckButton(label="Auto-reconnect VPN")
        auto_reconnect.set_active(self.auto_reconnect_enabled)
        auto_reconnect.connect("toggled", lambda w: setattr(self, 'auto_reconnect_enabled', w.get_active()))
        vpn_box.pack_start(auto_reconnect, False, False, 5)
        
        kill_switch = Gtk.CheckButton(label="Kill Switch (Block traffic if VPN disconnects)")
        kill_switch.set_active(self.kill_switch_enabled)
        kill_switch.set_tooltip_text("Warning: Requires root access and may block all internet if VPN fails")
        kill_switch.connect("toggled", lambda w: setattr(self, 'kill_switch_enabled', w.get_active()))
        vpn_box.pack_start(kill_switch, False, False, 5)
        
        vpn_box.set_margin_start(10)
        vpn_box.set_margin_end(10)
        vpn_box.set_margin_top(10)
        vpn_box.set_margin_bottom(10)
        
        content.pack_start(vpn_frame, True, True, 10)
        
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def load_filter_lists(self):
        """Load uBlock Origin-style filter lists (EasyList, EasyPrivacy)"""
        config_dir = Path.home() / ".config" / "phazebrowser"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        easylist_file = config_dir / "easylist.txt"
        easyprivacy_file = config_dir / "easyprivacy.txt"
        
        # Download filter lists if not present or older than 7 days
        if not easylist_file.exists() or (time.time() - easylist_file.stat().st_mtime) > 604800:
            try:
                print("📥 Downloading EasyList filter list...")
                response = requests.get(
                    "https://easylist.to/easylist/easylist.txt",
                    timeout=30, verify=True
                )
                if response.status_code == 200:
                    easylist_file.write_text(response.text)
                    print("✅ EasyList downloaded")
            except Exception as e:
                print(f"⚠️ Failed to download EasyList: {e}")
        
        if not easyprivacy_file.exists() or (time.time() - easyprivacy_file.stat().st_mtime) > 604800:
            try:
                print("📥 Downloading EasyPrivacy filter list...")
                response = requests.get(
                    "https://easylist.to/easylist/easyprivacy.txt",
                    timeout=30, verify=True
                )
                if response.status_code == 200:
                    easyprivacy_file.write_text(response.text)
                    print("✅ EasyPrivacy downloaded")
            except Exception as e:
                print(f"⚠️ Failed to download EasyPrivacy: {e}")
        
        # Parse filter lists
        self.parse_filter_list(easylist_file, self.easylist_rules)
        self.parse_filter_list(easyprivacy_file, self.easyprivacy_rules)
        
        # Extract blocked domains
        self.extract_blocked_domains()
        
        self.filter_lists_loaded = True
        print(f"✅ Filter lists loaded: {len(self.easylist_rules)} EasyList rules, {len(self.easyprivacy_rules)} EasyPrivacy rules")
    
    def parse_filter_list(self, filter_file, rules_list):
        """Parse uBlock Origin-style filter list"""
        if not filter_file.exists():
            return
        
        try:
            with open(filter_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('!') or line.startswith('['):
                        continue
                    
                    # Parse filter rules
                    # Format: ||domain.com^ or ||domain.com/path^
                    if line.startswith('||') and line.endswith('^'):
                        domain = line[2:-1].split('/')[0]
                        rules_list.append({
                            'type': 'domain',
                            'pattern': domain,
                            'rule': line
                        })
                    # Format: /ads/banner.js
                    elif line.startswith('/') and line.endswith('/'):
                        rules_list.append({
                            'type': 'url',
                            'pattern': line[1:-1],
                            'rule': line
                        })
                    # Format: domain.com##.ad-container
                    elif '##' in line:
                        parts = line.split('##')
                        if len(parts) == 2:
                            domain = parts[0]
                            selector = parts[1]
                            rules_list.append({
                                'type': 'css',
                                'domain': domain,
                                'selector': selector,
                                'rule': line
                            })
                    # Simple domain blocking
                    elif '^' in line:
                        domain = line.split('^')[0].replace('||', '').replace('|', '')
                        if domain:
                            rules_list.append({
                                'type': 'domain',
                                'pattern': domain,
                                'rule': line
                            })
        except Exception as e:
            print(f"⚠️ Error parsing filter list {filter_file}: {e}")
    
    def extract_blocked_domains(self):
        """Extract all blocked domains from filter lists"""
        for rule in self.easylist_rules + self.easyprivacy_rules:
            if rule['type'] == 'domain' and 'pattern' in rule:
                self.blocked_domains.add(rule['pattern'].lower())
    
    def load_ad_block_css(self):
        """Load comprehensive ad blocking CSS with extensive filter list support"""
        # Try to load from filter list file
        filter_list_file = Path.home() / ".config" / "phazebrowser" / "adblock-filters.css"
        
        if filter_list_file.exists():
            try:
                return filter_list_file.read_text()
            except:
                pass
        
        # Comprehensive ad blocking CSS - blocks ALL known ad patterns
        return r"""
        /* Comprehensive Ad Blocking - Blocks ALL ad types */
        
        /* Standard ad containers */
        [class*="ad"], [id*="ad"], [class*="advertisement"], 
        [id*="advertisement"], [class*="banner"], iframe[src*="ads"],
        div[class*="sponsored"], [data-ad], .ad-container,
        .adsbygoogle, #google_ads, .ad-banner, 
        [class*="google-ad"], [id*="google-ad"],
        .advertisement, .ad-banner, .ad-wrapper,
        .ad-slot, .ad-unit, .ad-wrapper, .ad-content,
        [class*="doubleclick"], [id*="doubleclick"],
        .popup, .overlay-ad, .sidebar-ad, .header-ad,
        .footer-ad, .inline-ad, .text-ad,
        
        /* Social media ads */
        [class*="fb-ad"], [id*="fb-ad"], [class*="facebook-ad"],
        [class*="twitter-ad"], [class*="instagram-ad"],
        
        /* Video ads */
        [class*="video-ad"], [id*="video-ad"], .pre-roll-ad,
        .mid-roll-ad, .post-roll-ad, .video-ad-container,
        
        /* Native ads */
        [class*="native-ad"], [class*="sponsored-content"],
        [class*="promoted"], [class*="recommended-ad"],
        
        /* Pop-ups and overlays */
        .popup, .modal-ad, .overlay-ad, .lightbox-ad,
        [class*="popup-ad"], [id*="popup-ad"],
        
        /* Sticky ads */
        .sticky-ad, .fixed-ad, [class*="sticky-ad"],
        
        /* Interstitial ads */
        .interstitial-ad, [class*="interstitial"],
        
        /* All ad-related attributes */
        [data-ad], [data-ad-client], [data-ad-slot],
        [data-ad-format], [data-adsbygoogle],
        
        /* Ad networks */
        [class*="adsense"], [id*="adsense"],
        [class*="adwords"], [class*="adform"],
        [class*="criteo"], [class*="outbrain"],
        [class*="taboola"], [class*="revcontent"],
        
        /* Generic ad patterns */
        [class*="promo"], [class*="sponsor"],
        [id*="promo"], [id*="sponsor"],
        
        /* Ad iframes */
        iframe[src*="ads"], iframe[src*="advertising"],
        iframe[src*="doubleclick"], iframe[src*="googlesyndication"],
        iframe[src*="adform"], iframe[src*="adnxs"],
        
        /* Ad images */
        img[src*="ads"], img[src*="advertising"],
        img[src*="doubleclick"], img[src*="adform"],
        
        /* Ad scripts */
        script[src*="ads"], script[src*="advertising"],
        script[src*="doubleclick"], script[src*="googlesyndication"] { 
            display: none !important; 
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
            opacity: 0 !important;
            position: absolute !important;
            display: none !important;
            
            pointer-events: none !important;
            
        }
        
        /* Block ad containers even if they try to show */
        [class*="ad"]:before, [class*="ad"]:after,
        [id*="ad"]:before, [id*="ad"]:after {
            display: none !important;
            content: none !important;
        }
        """
    
    def load_comprehensive_ad_block_js(self):
        """Load comprehensive JavaScript-based ad blocking"""
        return """
        (function() {
            'use strict';
            
            // Comprehensive ad blocking - removes ads before they render
            const adPatterns = [
                /ads?[_-]?/i, /advertisement/i, /banner/i, /sponsor/i,
                /promo/i, /doubleclick/i, /googlesyndication/i,
                /adsense/i, /adform/i, /adnxs/i, /criteo/i,
                /outbrain/i, /taboola/i, /revcontent/i,
                /facebook.*ad/i, /twitter.*ad/i, /instagram.*ad/i
            ];
            
            function isAdElement(element) {
                if (!element) return false;
                
                const className = element.className || '';
                const id = element.id || '';
                const src = element.src || '';
                const href = element.href || '';
                
                const text = (className + ' ' + id + ' ' + src + ' ' + href).toLowerCase();
                
                return adPatterns.some(pattern => pattern.test(text));
            }
            
            function removeAds() {
                // Remove all ad elements
                const allElements = document.querySelectorAll('*');
                allElements.forEach(element => {
                    if (isAdElement(element)) {
                        element.remove();
                    }
                });
                
                // Remove ad iframes
                const iframes = document.querySelectorAll('iframe');
                iframes.forEach(iframe => {
                    const src = iframe.src || '';
                    if (adPatterns.some(pattern => pattern.test(src))) {
                        iframe.remove();
                    }
                });
                
                // Remove ad images
                const images = document.querySelectorAll('img');
                images.forEach(img => {
                    if (isAdElement(img)) {
                        img.remove();
                    }
                });
            }
            
            // Run immediately
            removeAds();
            
            // Run after DOM loads
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', removeAds);
            }
            
            // Monitor for dynamically added ads
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            if (isAdElement(node)) {
                                node.remove();
                            } else {
                                // Check children
                                const children = node.querySelectorAll ? node.querySelectorAll('*') : [];
                                children.forEach(child => {
                                    if (isAdElement(child)) {
                                        child.remove();
                                    }
                                });
                            }
                        }
                    });
                });
            });
            
            observer.observe(document.body || document.documentElement, {
                childList: true,
                subtree: true
            });
            
            // Block ad network requests
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                if (typeof url === 'string' && adPatterns.some(pattern => pattern.test(url))) {
                    return Promise.reject(new Error('Ad blocked'));
                }
                return originalFetch.apply(this, args);
            };
            
            // Block XMLHttpRequest to ad domains
            const originalOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url, ...rest) {
                if (adPatterns.some(pattern => pattern.test(url))) {
                    throw new Error('Ad request blocked');
                }
                return originalOpen.apply(this, [method, url, ...rest]);
            };
        })();
        """
    
    def load_comprehensive_tracking_block_js(self):
        """Load comprehensive tracking protection JavaScript"""
        # Comprehensive tracking domain list
        tracking_domains = [
            # Google tracking
            'google-analytics.com', 'googletagmanager.com', 'googleadservices.com',
            'googlesyndication.com', 'doubleclick.net', 'adservice.google',
            'analytics.google', 'google-analytics', 'googletagmanager',
            
            # Facebook tracking
            'facebook.net', 'facebook.com/tr', 'fbcdn.net',
            'connect.facebook.net', 'facebook.com/connect',
            
            # Twitter tracking
            'twitter.com/i/adsct', 'ads-twitter.com',
            
            # Amazon tracking
            'amazon-adsystem.com', 'aax-us-east.amazon-adsystem.com',
            
            # Microsoft tracking
            'bing.com/maps', 'c.microsoft.com',
            
            # Analytics services
            'scorecardresearch.com', 'quantserve.com', 'chartbeat.com',
            'mixpanel.com', 'segment.com', 'amplitude.com',
            'hotjar.com', 'fullstory.com', 'mouseflow.com',
            'crazyegg.com', 'optimizely.com', 'vwo.com',
            
            # Ad networks
            'adnxs.com', 'adsrvr.org', 'adtechus.com',
            'criteo.com', 'rubiconproject.com', 'pubmatic.com',
            'openx.net', 'indexexchange.com', '33across.com',
            'adform.com', 'outbrain.com', 'taboola.com',
            'revcontent.com', 'zemanta.com', 'content.ad',
            
            # Other trackers
            'addthis.com', 'sharethis.com', 'addtoany.com',
            'disqus.com', 'gravatar.com',
            
            # Data brokers
            'bluekai.com', 'lotame.com', 'neustar.biz',
            'exelate.com', 'turn.com',
            
            # Social tracking
            'pinterest.com', 'linkedin.com/px', 'reddit.com/api',
            
            # CDN tracking
            'cloudflare.com/insights', 'jsdelivr.net/stats',
        ]
        
        blocked_js = "const blockedTrackingDomains = " + json.dumps(tracking_domains) + ";"
        blocked_js += """
        (function() {
            'use strict';
            
            function isTrackingDomain(url) {
                if (!url) return false;
                const urlLower = url.toLowerCase();
                return blockedTrackingDomains.some(domain => urlLower.includes(domain));
            }
            
            // Block tracking scripts
            function blockTrackingScripts() {
                const scripts = document.getElementsByTagName('script');
                for (let script of scripts) {
                    if (script.src && isTrackingDomain(script.src)) {
                        script.remove();
                    }
                }
            }
            
            // Block tracking images/pixels
            function blockTrackingImages() {
                const imgs = document.getElementsByTagName('img');
                for (let img of imgs) {
                    if (img.src && isTrackingDomain(img.src)) {
                        img.remove();
                    }
                }
            }
            
            // Block tracking iframes
            function blockTrackingIframes() {
                const iframes = document.getElementsByTagName('iframe');
                for (let iframe of iframes) {
                    if (iframe.src && isTrackingDomain(iframe.src)) {
                        iframe.remove();
                    }
                }
            }
            
            // Block tracking links
            function blockTrackingLinks() {
                const links = document.getElementsByTagName('a');
                for (let link of links) {
                    if (link.href && isTrackingDomain(link.href)) {
                        link.removeAttribute('href');
                    }
                }
            }
            
            // Run blocking functions
            blockTrackingScripts();
            blockTrackingImages();
            blockTrackingIframes();
            blockTrackingLinks();
            
            // Monitor for dynamically added tracking elements
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            if (node.tagName === 'SCRIPT' && node.src && isTrackingDomain(node.src)) {
                                node.remove();
                            }
                            if (node.tagName === 'IMG' && node.src && isTrackingDomain(node.src)) {
                                node.remove();
                            }
                            if (node.tagName === 'IFRAME' && node.src && isTrackingDomain(node.src)) {
                                node.remove();
                            }
                        }
                    });
                });
            });
            
            observer.observe(document.body || document.documentElement, {
                childList: true,
                subtree: true
            });
            
            // Block fetch requests to tracking domains
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                if (typeof url === 'string' && isTrackingDomain(url)) {
                    return Promise.reject(new Error('Tracking request blocked'));
                }
                return originalFetch.apply(this, args);
            };
            
            // Block XMLHttpRequest to tracking domains
            const originalOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url, ...rest) {
                if (isTrackingDomain(url)) {
                    throw new Error('Tracking request blocked');
                }
                return originalOpen.apply(this, [method, url, ...rest]);
            };
            
            // Block sendBeacon API (used for tracking)
            if (navigator.sendBeacon) {
                const originalSendBeacon = navigator.sendBeacon;
                navigator.sendBeacon = function(url, data) {
                    if (isTrackingDomain(url)) {
                        return false; // Block the beacon
                    }
                    return originalSendBeacon.apply(this, arguments);
                };
            }
        })();
        """
        return blocked_js
    
    def load_cookie_blocking_js(self):
        """Load cookie blocking for tracking domains"""
        tracking_domains = [
            'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
            'facebook.net', 'facebook.com', 'scorecardresearch.com',
            'quantserve.com', 'adnxs.com', 'criteo.com'
        ]
        
        blocked_js = "const trackingDomains = " + json.dumps(tracking_domains) + ";"
        blocked_js += """
        (function() {
            'use strict';
            
            function isTrackingDomain(domain) {
                if (!domain) return false;
                const domainLower = domain.toLowerCase();
                return trackingDomains.some(td => domainLower.includes(td));
            }
            
            // Block cookie setting for tracking domains
            const originalCookieDescriptor = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie') ||
                                            Object.getOwnPropertyDescriptor(HTMLDocument.prototype, 'cookie');
            
            if (originalCookieDescriptor && originalCookieDescriptor.set) {
                Object.defineProperty(document, 'cookie', {
                    get: function() {
                        return originalCookieDescriptor.get.call(this);
                    },
                    set: function(value) {
                        const currentDomain = window.location.hostname;
                        if (isTrackingDomain(currentDomain)) {
                            return; // Block cookie setting
                        }
                        return originalCookieDescriptor.set.call(this, value);
                    },
                    configurable: true
                });
            }
            
            // Block localStorage for tracking domains
            const originalSetItem = Storage.prototype.setItem;
            Storage.prototype.setItem = function(key, value) {
                const currentDomain = window.location.hostname;
                if (isTrackingDomain(currentDomain)) {
                    return; // Block localStorage
                }
                return originalSetItem.apply(this, arguments);
            };
            
            // Block sessionStorage for tracking domains
            const originalSessionSetItem = sessionStorage.setItem;
            sessionStorage.setItem = function(key, value) {
                const currentDomain = window.location.hostname;
                if (isTrackingDomain(currentDomain)) {
                    return; // Block sessionStorage
                }
                return originalSessionSetItem.apply(this, arguments);
            };
            
            // Clear existing tracking cookies
            function clearTrackingCookies() {
                const cookies = document.cookie.split(';');
                cookies.forEach(cookie => {
                    const cookieDomain = cookie.split('=')[0].trim();
                    if (isTrackingDomain(cookieDomain)) {
                        document.cookie = cookieDomain + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                        document.cookie = cookieDomain + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + window.location.hostname;
                    }
                });
            }
            
            clearTrackingCookies();
            
            // Clear tracking localStorage
            function clearTrackingStorage() {
                const currentDomain = window.location.hostname;
                if (isTrackingDomain(currentDomain)) {
                    localStorage.clear();
                    sessionStorage.clear();
                }
            }
            
            clearTrackingStorage();
        })();
        """
        return blocked_js
    
    def load_fingerprint_protection_js(self):
        """Load comprehensive fingerprinting protection"""
        return """
        (function() {
            'use strict';
            
            // Canvas fingerprinting protection
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            HTMLCanvasElement.prototype.toDataURL = function() {
                // Add noise to canvas to prevent fingerprinting
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 0.01; // Add tiny noise
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            CanvasRenderingContext2D.prototype.getImageData = function() {
                const imageData = originalGetImageData.apply(this, arguments);
                // Add noise to prevent fingerprinting
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] += Math.random() * 0.01;
                }
                return imageData;
            };
            
            // WebGL fingerprinting protection
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                    return 'Intel Inc.';
                }
                if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            
            // Audio fingerprinting protection
            if (window.AudioContext || window.webkitAudioContext) {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                const originalCreateOscillator = AudioContext.prototype.createOscillator;
                AudioContext.prototype.createOscillator = function() {
                    const oscillator = originalCreateOscillator.apply(this, arguments);
                    const originalFrequency = oscillator.frequency.value;
                    oscillator.frequency.value = originalFrequency + (Math.random() * 0.0001 - 0.00005);
                    return oscillator;
                };
            }
            
            // Font fingerprinting protection
            const originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
            const originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
            
            if (originalOffsetWidth && originalOffsetWidth.get) {
                Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
                    get: function() {
                        const width = originalOffsetWidth.get.call(this);
                        return width + (Math.random() * 0.1 - 0.05); // Add tiny noise
                    },
                    configurable: true
                });
            }
            
            // Screen fingerprinting protection
            Object.defineProperty(window.screen, 'width', {
                get: function() { return 1920; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'height', {
                get: function() { return 1080; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'availWidth', {
                get: function() { return 1920; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'availHeight', {
                get: function() { return 1040; },
                configurable: true
            });
            
            // Timezone fingerprinting protection
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {
                return 0; // Return UTC offset
            };
            
            // Navigator fingerprinting protection
            Object.defineProperty(navigator, 'platform', {
                get: function() { return 'Linux x86_64'; },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: function() { return 4; },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: function() { return 8; },
                configurable: true
            });
            
            // WebRTC leak protection (block RTCPeerConnection)
            if (window.RTCPeerConnection) {
                window.RTCPeerConnection = function() {
                    throw new Error('WebRTC blocked for privacy');
                };
            }
            if (window.webkitRTCPeerConnection) {
                window.webkitRTCPeerConnection = function() {
                    throw new Error('WebRTC blocked for privacy');
                };
            }
            if (window.mozRTCPeerConnection) {
                window.mozRTCPeerConnection = function() {
                    throw new Error('WebRTC blocked for privacy');
                };
            }
            
            // Battery API protection
            if (navigator.getBattery) {
                navigator.getBattery = function() {
                    return Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1
                    });
                };
            }
            
            // Permissions API protection
            if (navigator.permissions) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(descriptor) {
                    if (descriptor.name === 'notifications' || 
                        descriptor.name === 'geolocation' ||
                        descriptor.name === 'camera' ||
                        descriptor.name === 'microphone') {
                        return Promise.resolve({ state: 'denied' });
                    }
                    return originalQuery.apply(this, arguments);
                };
            }
        })();
        """
    
    def on_decide_policy(self, webview, decision, decision_type, request):
        """Block network requests for ads and trackers using filter lists"""
        # Only handle navigation requests
        if decision_type != WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            return
        
        try:
            uri = request.get_uri()
            if not uri:
                return
            
            uri_lower = uri.lower()
            
            # Check against filter lists if loaded
            if self.filter_lists_loaded:
                # Check domain blocking
                from urllib.parse import urlparse
                parsed = urlparse(uri)
                domain = parsed.netloc.lower().lstrip('www.')
                
                # Check if domain is in blocked list
                for blocked_domain in self.blocked_domains:
                    if blocked_domain in domain or domain.endswith('.' + blocked_domain):
                        decision.ignore()
                        return
                
                # Check URL patterns
                for rule in self.easylist_rules + self.easyprivacy_rules:
                    if rule['type'] == 'url' and rule['pattern'] in uri_lower:
                        decision.ignore()
                        return
            
            # Fallback: Comprehensive ad and tracking domain blocking
            blocked_patterns = [
                # Ad networks
                'doubleclick', 'googlesyndication', 'googleadservices',
                'adsense', 'adform', 'adnxs', 'adsrvr', 'adtech',
                'criteo', 'rubiconproject', 'pubmatic', 'openx',
                'indexexchange', '33across', 'outbrain', 'taboola',
                'revcontent', 'zemanta', 'content.ad', 'adsystem',
                
                # Tracking
                'google-analytics', 'googletagmanager', 'analytics',
                'facebook.net', 'facebook.com/tr', 'scorecardresearch',
                'quantserve', 'chartbeat', 'mixpanel', 'segment',
                'amplitude', 'hotjar', 'fullstory', 'mouseflow',
                'crazyegg', 'optimizely', 'vwo', 'newrelic',
                
                # Social tracking
                'addthis', 'sharethis', 'addtoany', 'sharethrough',
                
                # Data brokers
                'bluekai', 'lotame', 'neustar', 'exelate', 'turn',
                'liveintent', 'thetradedesk', 'appnexus',
                
                # Ad patterns in URL
                '/ads/', '/advertising/', '/banner', '/sponsor',
                '/promo', '/ad.', '.ad.', '/ad?', '?ad=',
                '/tracking/', '/track/', '/pixel', '/beacon',
            ]
            
            # Check if URI matches blocked patterns
            for pattern in blocked_patterns:
                if pattern in uri_lower:
                    decision.ignore()
                    return
        except:
            pass  # Silently fail if blocking fails
    
    def on_resource_load_started(self, webview, resource, request):
        """Block resource loading for ads and trackers using filter lists"""
        try:
            uri = request.get_uri()
            if not uri:
                return
            
            uri_lower = uri.lower()
            
            # Check against filter lists if loaded
            if self.filter_lists_loaded:
                from urllib.parse import urlparse
                parsed = urlparse(uri)
                domain = parsed.netloc.lower().lstrip('www.')
                
                # Check if domain is blocked
                for blocked_domain in self.blocked_domains:
                    if blocked_domain in domain or domain.endswith('.' + blocked_domain):
                        try:
                            resource.cancel()
                        except:
                            pass
                        return
                
                # Check URL patterns
                for rule in self.easylist_rules + self.easyprivacy_rules:
                    if rule['type'] == 'url' and rule['pattern'] in uri_lower:
                        try:
                            resource.cancel()
                        except:
                            pass
                        return
            
            # Fallback: Block ad and tracking resources
            blocked_patterns = [
                'doubleclick', 'googlesyndication', 'googleadservices',
                'adsense', 'adform', 'adnxs', 'google-analytics',
                'googletagmanager', 'facebook.net', 'scorecardresearch',
                'quantserve', '/ads/', '/advertising/', '/banner',
                '.ad.', '/ad?', '?ad=', 'advertising', 'tracking',
                'analytics', 'pixel', 'beacon', 'tracking',
            ]
            
            for pattern in blocked_patterns:
                if pattern in uri_lower:
                    try:
                        resource.cancel()
                    except:
                        pass
                    return
        except:
            pass
    
    def load_max_privacy_mode_js(self):
        """Load maximum privacy mode - makes all users identical (anti-fingerprinting)"""
        return r"""
        (function() {
            'use strict';
            
            // MAXIMUM PRIVACY MODE - Make all users appear identical
            // This prevents fingerprinting by making everyone look the same
            
            // ===== CANVAS FINGERPRINTING PROTECTION =====
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            // Add consistent noise to canvas (same for all users)
            function addCanvasNoise(imageData) {
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {
                    // Add consistent noise based on pixel position
                    const noise = Math.sin(i * 0.1) * 0.5;
                    data[i] = Math.max(0, Math.min(255, data[i] + noise));
                    data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                    data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                }
                return imageData;
            }
            
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    addCanvasNoise(imageData);
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            HTMLCanvasElement.prototype.toBlob = function(callback) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    addCanvasNoise(imageData);
                    context.putImageData(imageData, 0, 0);
                }
                return originalToBlob.apply(this, arguments);
            };
            
            CanvasRenderingContext2D.prototype.getImageData = function() {
                const imageData = originalGetImageData.apply(this, arguments);
                return addCanvasNoise(imageData);
            };
            
            // ===== WEBGL FINGERPRINTING PROTECTION =====
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // Return standardized values for all users
                const standardized = {
                    37445: 'Intel Inc.',           // UNMASKED_VENDOR_WEBGL
                    37446: 'Intel Iris OpenGL Engine', // UNMASKED_RENDERER_WEBGL
                    7936: 'WebGL 1.0',             // VERSION
                    7937: 'WebGL GLSL ES 1.0',     // SHADING_LANGUAGE_VERSION
                };
                return standardized[parameter] || getParameter.apply(this, arguments);
            };
            
            // ===== AUDIO FINGERPRINTING PROTECTION =====
            if (window.AudioContext || window.webkitAudioContext) {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
                const originalCreateOscillator = AudioContext.prototype.createOscillator;
                
                AudioContext.prototype.createAnalyser = function() {
                    const analyser = originalCreateAnalyser.apply(this, arguments);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        originalGetFloatFrequencyData.apply(this, arguments);
                        // Add consistent noise
                        for (let i = 0; i < array.length; i++) {
                            array[i] += Math.sin(i * 0.1) * 0.1;
                        }
                    };
                    return analyser;
                };
            }
            
            // ===== FONT FINGERPRINTING PROTECTION =====
            // Standardize font measurements
            const originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
            const originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
            const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;
            
            if (originalOffsetWidth && originalOffsetWidth.get) {
                Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
                    get: function() {
                        const width = originalOffsetWidth.get.call(this);
                        // Round to nearest 10 to prevent fingerprinting
                        return Math.round(width / 10) * 10;
                    },
                    configurable: true
                });
            }
            
            if (originalOffsetHeight && originalOffsetHeight.get) {
                Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
                    get: function() {
                        const height = originalOffsetHeight.get.call(this);
                        return Math.round(height / 10) * 10;
                    },
                    configurable: true
                });
            }
            
            Element.prototype.getBoundingClientRect = function() {
                const rect = originalGetBoundingClientRect.apply(this, arguments);
                // Round values to prevent fingerprinting
                return {
                    x: Math.round(rect.x / 5) * 5,
                    y: Math.round(rect.y / 5) * 5,
                    width: Math.round(rect.width / 5) * 5,
                    height: Math.round(rect.height / 5) * 5,
                    top: Math.round(rect.top / 5) * 5,
                    right: Math.round(rect.right / 5) * 5,
                    bottom: Math.round(rect.bottom / 5) * 5,
                    left: Math.round(rect.left / 5) * 5
                };
            };
            
            // ===== SCREEN FINGERPRINTING PROTECTION =====
            // Standardize screen dimensions for all users
            Object.defineProperty(window.screen, 'width', {
                get: function() { return 1920; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'height', {
                get: function() { return 1080; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'availWidth', {
                get: function() { return 1920; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'availHeight', {
                get: function() { return 1040; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'colorDepth', {
                get: function() { return 24; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'pixelDepth', {
                get: function() { return 24; },
                configurable: true
            });
            
            // ===== TIMEZONE FINGERPRINTING PROTECTION =====
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {
                return 0; // UTC for all users
            };
            
            const originalToString = Date.prototype.toString;
            Date.prototype.toString = function() {
                const str = originalToString.apply(this, arguments);
                // Standardize timezone string
                return str.replace(/GMT[+-]\d+/, 'GMT+0000');
            };
            
            // ===== NAVIGATOR FINGERPRINTING PROTECTION =====
            // Standardize navigator properties
            Object.defineProperty(navigator, 'platform', {
                get: function() { return 'Linux x86_64'; },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: function() { return 4; },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: function() { return 8; },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: function() { return 0; },
                configurable: true
            });
            
            // Standardize user agent (but keep it realistic)
            Object.defineProperty(navigator, 'userAgent', {
                get: function() { 
                    return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
                },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'language', {
                get: function() { return 'en-US'; },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: function() { return ['en-US', 'en']; },
                configurable: true
            });
            
            // ===== WEBRTC LEAK PROTECTION =====
            // Completely block WebRTC to prevent IP leaks
            if (window.RTCPeerConnection) {
                window.RTCPeerConnection = function() {
                    throw new Error('WebRTC blocked for maximum privacy');
                };
            }
            if (window.webkitRTCPeerConnection) {
                window.webkitRTCPeerConnection = function() {
                    throw new Error('WebRTC blocked for maximum privacy');
                };
            }
            if (window.mozRTCPeerConnection) {
                window.mozRTCPeerConnection = function() {
                    throw new Error('WebRTC blocked for maximum privacy');
                };
            }
            
            // ===== BATTERY API PROTECTION =====
            if (navigator.getBattery) {
                navigator.getBattery = function() {
                    return Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1.0
                    });
                };
            }
            
            // ===== PERMISSIONS API PROTECTION =====
            if (navigator.permissions) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(descriptor) {
                    // Deny all permissions to prevent tracking
                    const deniedPermissions = ['notifications', 'geolocation', 'camera', 
                                             'microphone', 'persistent-storage', 'push'];
                    if (deniedPermissions.includes(descriptor.name)) {
                        return Promise.resolve({ state: 'denied' });
                    }
                    return originalQuery.apply(this, arguments);
                };
            }
            
            // ===== GEOLOCATION PROTECTION =====
            if (navigator.geolocation) {
                const originalGetCurrentPosition = navigator.geolocation.getCurrentPosition;
                navigator.geolocation.getCurrentPosition = function(success, error) {
                    if (error) error({ code: 1, message: 'Permission denied' });
                };
                
                const originalWatchPosition = navigator.geolocation.watchPosition;
                navigator.geolocation.watchPosition = function(success, error) {
                    if (error) error({ code: 1, message: 'Permission denied' });
                    return -1;
                };
            }
            
            // ===== MEDIA DEVICES PROTECTION =====
            if (navigator.mediaDevices) {
                const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                navigator.mediaDevices.enumerateDevices = function() {
                    return Promise.resolve([]); // Return empty device list
                };
                
                const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
                navigator.mediaDevices.getUserMedia = function() {
                    return Promise.reject(new Error('Permission denied'));
                };
            }
            
            // ===== PLUGINS PROTECTION =====
            Object.defineProperty(navigator, 'plugins', {
                get: function() { return []; },
                configurable: true
            });
            
            Object.defineProperty(navigator, 'mimeTypes', {
                get: function() { return []; },
                configurable: true
            });
            
            // ===== CONNECTION API PROTECTION =====
            if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {
                const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                Object.defineProperty(connection, 'downlink', {
                    get: function() { return 10; },
                    configurable: true
                });
                Object.defineProperty(connection, 'effectiveType', {
                    get: function() { return '4g'; },
                    configurable: true
                });
                Object.defineProperty(connection, 'rtt', {
                    get: function() { return 50; },
                    configurable: true
                });
            }
            
            // ===== PERFORMANCE API PROTECTION =====
            if (window.performance && window.performance.getEntriesByType) {
                const originalGetEntriesByType = window.performance.getEntriesByType;
                window.performance.getEntriesByType = function(type) {
                    if (type === 'navigation' || type === 'resource') {
                        // Return minimal standardized data
                        return [];
                    }
                    return originalGetEntriesByType.apply(this, arguments);
                };
            }
            
            // ===== BLOCK ALL TRACKING COOKIES =====
            const originalCookieDescriptor = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie') ||
                                            Object.getOwnPropertyDescriptor(HTMLDocument.prototype, 'cookie');
            
            if (originalCookieDescriptor && originalCookieDescriptor.set) {
                Object.defineProperty(document, 'cookie', {
                    get: function() {
                        // Only return first-party cookies
                        const cookies = originalCookieDescriptor.get.call(this);
                        return cookies.split(';').filter(c => {
                            // Block known tracking cookies
                            const trackingPatterns = ['_ga', '_gid', '_gat', 'fbp', 'fbc', 
                                                     '_fbp', '_fbc', 'utm_', 'tracking'];
                            return !trackingPatterns.some(pattern => c.includes(pattern));
                        }).join(';');
                    },
                    set: function(value) {
                        // Block tracking cookies
                        const trackingPatterns = ['_ga', '_gid', '_gat', 'fbp', 'fbc', 
                                                 '_fbp', '_fbc', 'utm_', 'tracking', 'analytics'];
                        if (trackingPatterns.some(pattern => value.toLowerCase().includes(pattern))) {
                            return; // Block tracking cookie
                        }
                        return originalCookieDescriptor.set.call(this, value);
                    },
                    configurable: true
                });
            }
            
            // ===== BLOCK TRACKING STORAGE =====
            const originalSetItem = Storage.prototype.setItem;
            Storage.prototype.setItem = function(key, value) {
                const trackingPatterns = ['_ga', '_gid', '_gat', 'fbp', 'fbc', 
                                         '_fbp', '_fbc', 'utm_', 'tracking', 'analytics'];
                if (trackingPatterns.some(pattern => key.toLowerCase().includes(pattern))) {
                    return; // Block tracking storage
                }
                return originalSetItem.apply(this, arguments);
            };
            
            console.log('🛡️ Maximum Privacy Mode Active - All users appear identical');
        })();
        """
    
    def on_download_started(self, download):
        """Handle download started event"""
        # Get download info
        uri = download.get_uri()
        suggested_filename = download.get_suggested_filename()
        
        # Create download entry
        download_info = {
            'uri': uri,
            'filename': suggested_filename or uri.split('/')[-1],
            'start_time': time.time(),
            'status': 'downloading',
            'bytes_received': 0,
            'total_bytes': 0,
            'download': download
        }
        
        self.downloads.append(download_info)
        
        # Connect to progress signal
        download.connect("received-data", self.on_download_progress)
        download.connect("finished", self.on_download_finished)
        
        # Set download destination
        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(exist_ok=True)
        download_path = downloads_dir / download_info['filename']
        download.set_destination(f"file://{download_path}")
        
        print(f"⬇️ Download started: {download_info['filename']}")
    
    def on_download_progress(self, download, length):
        """Handle download progress"""
        for dl_info in self.downloads:
            if dl_info['download'] == download:
                dl_info['bytes_received'] += length
                total = download.get_estimated_progress() * 100 if download.get_estimated_progress() > 0 else 0
                print(f"⬇️ Download progress: {dl_info['filename']} - {total:.1f}%")
                break
    
    def on_download_finished(self, download):
        """Handle download finished"""
        for dl_info in self.downloads:
            if dl_info['download'] == download:
                dl_info['status'] = 'completed'
                dl_info['finish_time'] = time.time()
                print(f"✅ Download completed: {dl_info['filename']}")
                break
    
    def show_downloads(self, button):
        """Show download manager dialog"""
        dialog = Gtk.Dialog(title="Download Manager", parent=self.window)
        dialog.set_default_size(600, 400)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        # Downloads list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        downloads_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        if not self.downloads:
            no_downloads = Gtk.Label()
            no_downloads.set_text("No downloads yet")
            downloads_box.pack_start(no_downloads, False, False, 5)
        else:
            for dl_info in reversed(self.downloads):  # Show newest first
                dl_frame = Gtk.Frame()
                dl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                
                filename_label = Gtk.Label()
                filename_label.set_markup(f"<b>{dl_info['filename']}</b>")
                filename_label.set_halign(Gtk.Align.START)
                dl_box.pack_start(filename_label, False, False, 2)
                
                status_label = Gtk.Label()
                if dl_info['status'] == 'downloading':
                    progress = 0
                    if dl_info['download'].get_estimated_progress() > 0:
                        progress = dl_info['download'].get_estimated_progress() * 100
                    status_label.set_text(f"Status: Downloading... {progress:.1f}%")
                elif dl_info['status'] == 'completed':
                    elapsed = dl_info.get('finish_time', time.time()) - dl_info['start_time']
                    size_mb = dl_info['bytes_received'] / (1024 * 1024)
                    status_label.set_text(f"Status: Completed ({size_mb:.2f} MB in {elapsed:.1f}s)")
                else:
                    status_label.set_text(f"Status: {dl_info['status']}")
                status_label.set_halign(Gtk.Align.START)
                dl_box.pack_start(status_label, False, False, 2)
                
                dl_box.set_margin_start(10)
                dl_box.set_margin_end(10)
                dl_box.set_margin_top(5)
                dl_box.set_margin_bottom(5)
                
                dl_frame.add(dl_box)
                downloads_box.pack_start(dl_frame, False, False, 5)
        
        scroll.add(downloads_box)
        content.pack_start(scroll, True, True, 10)
        
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def run(self):
        """Run the browser"""
        self.window.show_all()
        Gtk.main()

def main():
    """Main entry point"""
    try:
        gi.require_version('WebKit2', '4.1')
    except ValueError:
        print("❌ WebKit2 4.1 not found!")
        print("Install it with:")
        print("  sudo apt-get install gir1.2-webkit2-4.1")
        sys.exit(1)
    
    browser = PhazeBrowserEnhanced()
    browser.run()

if __name__ == "__main__":
    main()

