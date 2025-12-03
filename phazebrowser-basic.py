#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhazeBrowser - VPN-Native Secure Browser
A custom browser that routes ALL traffic through the VPN
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')

from gi.repository import Gtk, WebKit2, GLib
import subprocess
import threading
import time
from pathlib import Path
import os
import sys

class PhazeBrowser:
    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_title("PhazeBrowser - Secure VPN Browser")
        self.window.set_default_size(1200, 800)
        self.window.connect("destroy", Gtk.main_quit)
        
        # VPN status
        self.vpn_connected = False
        self.vpn_interface = None
        self.check_vpn_interval = 2  # Check every 2 seconds
        
        # Check VPN status
        self.check_vpn_status()
        
        # Create UI
        self.create_ui()
        
        # Start VPN monitoring
        self.start_vpn_monitoring()
    
    def check_vpn_status(self):
        """Check if VPN is connected"""
        try:
            # Check for OpenVPN interface (tun0, tun1, etc.)
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True, text=True, timeout=2)
            
            # Look for tun interfaces
            for line in result.stdout.split('\n'):
                if 'tun' in line.lower() and 'state UP' in line:
                    # Extract interface name
                    parts = line.split(':')
                    if len(parts) >= 2:
                        self.vpn_interface = parts[1].strip().split()[0]
                        self.vpn_connected = True
                        return True
            
            # Also check OpenVPN process
            result = subprocess.run(['pgrep', '-f', 'openvpn'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Check if interface exists
                result = subprocess.run(['ip', 'addr', 'show'], 
                                      capture_output=True, text=True, timeout=2)
                if 'tun' in result.stdout:
                    self.vpn_connected = True
                    # Find tun interface
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
            self.vpn_status_label.set_text(f"🟢 VPN Connected ({self.vpn_interface})")
            self.vpn_status_label.set_name("vpn-connected")
            # Allow browsing
            self.webview.set_sensitive(True)
        else:
            self.vpn_status_label.set_text("🔴 VPN Disconnected - Browsing Blocked")
            self.vpn_status_label.set_name("vpn-disconnected")
            # Block browsing
            self.webview.set_sensitive(False)
            # Show warning page
            self.show_vpn_warning()
    
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
        self.webview.load_html(warning_html, "file:///")
    
    def create_ui(self):
        """Create the browser UI"""
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(vbox)
        
        # VPN Status Bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_bar.set_margin_start(10)
        status_bar.set_margin_end(10)
        status_bar.set_margin_top(5)
        status_bar.set_margin_bottom(5)
        
        self.vpn_status_label = Gtk.Label()
        self.vpn_status_label.set_markup("<b>Checking VPN...</b>")
        status_bar.pack_start(self.vpn_status_label, False, False, 0)
        
        refresh_btn = Gtk.Button(label="🔄 Refresh Status")
        refresh_btn.connect("clicked", lambda w: self.check_vpn_status())
        refresh_btn.connect("clicked", lambda w: self.update_vpn_status())
        status_bar.pack_end(refresh_btn, False, False, 0)
        
        vbox.pack_start(status_bar, False, False, 0)
        
        # Navigation Bar
        nav_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        nav_bar.set_margin_start(10)
        nav_bar.set_margin_end(10)
        nav_bar.set_margin_bottom(5)
        
        back_btn = Gtk.Button(label="◀")
        back_btn.connect("clicked", lambda w: self.webview.go_back())
        nav_bar.pack_start(back_btn, False, False, 0)
        
        forward_btn = Gtk.Button(label="▶")
        forward_btn.connect("clicked", lambda w: self.webview.go_forward())
        nav_bar.pack_start(forward_btn, False, False, 0)
        
        refresh_web_btn = Gtk.Button(label="🔄")
        refresh_web_btn.connect("clicked", lambda w: self.webview.reload())
        nav_bar.pack_start(refresh_web_btn, False, False, 0)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter URL or search...")
        self.url_entry.connect("activate", self.on_url_activate)
        nav_bar.pack_start(self.url_entry, True, True, 0)
        
        go_btn = Gtk.Button(label="Go")
        go_btn.connect("clicked", self.on_go_clicked)
        nav_bar.pack_start(go_btn, False, False, 0)
        
        vbox.pack_start(nav_bar, False, False, 0)
        
        # WebView
        self.webview = WebKit2.WebView()
        self.webview.connect("load-changed", self.on_load_changed)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.webview)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Load initial page
        if self.vpn_connected:
            self.webview.load_uri("https://www.google.com")
        else:
            self.show_vpn_warning()
        
        # Update status
        self.update_vpn_status()
    
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
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                # Search query
                url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        
        self.webview.load_uri(url)
    
    def on_load_changed(self, webview, load_event):
        """Handle page load events"""
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = webview.get_uri()
            if uri:
                self.url_entry.set_text(uri)
    
    def run(self):
        """Run the browser"""
        self.window.show_all()
        Gtk.main()

def main():
    """Main entry point"""
    # Check if WebKit2 is available
    try:
        gi.require_version('WebKit2', '4.1')
    except ValueError:
        print("❌ WebKit2 4.1 not found!")
        print("Install it with:")
        print("  sudo apt-get install gir1.2-webkit2-4.1")
        sys.exit(1)
    
    # Check if VPN config exists
    config_paths = [
        Path.home() / ".config" / "phazevpn" / "client.ovpn",
        Path("/etc/phazevpn/client.ovpn"),
        Path("/opt/phaze-vpn/client-configs"),
    ]
    
    has_config = any(p.exists() for p in config_paths)
    
    if not has_config:
        print("⚠️  No VPN config found. Browser will work but VPN routing may not be active.")
        print("   Place your .ovpn config in one of:")
        for p in config_paths:
            print(f"     - {p}")
    
    # Create and run browser
    browser = PhazeBrowser()
    browser.run()

if __name__ == "__main__":
    main()

