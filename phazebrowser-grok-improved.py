#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhazeBrowser: Secure VPN-Native Browser with Privacy Features
Custom GTK/WebKit2 browser with baked-in VPN, ad/tracking block, anti-fingerprinting.
Improved version with better VPN integration and OpenVPN support
"""

import sys
import os
import time
import json
import threading
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Install requests: pip3 install requests")
    sys.exit(1)

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('WebKit2', '4.1')
    from gi.repository import Gtk, Gdk, WebKit2, GLib
except ImportError as e:
    print(f"GTK/WebKit missing: {e}")
    print("Install: sudo apt-get install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1")
    sys.exit(1)

import subprocess

class PhazeBrowser:
    def __init__(self):
        self.window = Gtk.Window(title="PhazeBrowser - Secure VPN Browser")
        self.window.set_default_size(1200, 800)
        self.window.connect("destroy", Gtk.main_quit)

        self.vpn_connected = False
        self.vpn_process = None
        self.config_dir = Path.home() / ".config" / "phazebrowser"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings = self.load_settings()
        self.tabs = []
        self.filter_rules = {"ad": [], "track": []}

        self.load_privacy_filters()
        threading.Thread(target=self.vpn_monitor, daemon=True).start()

        self.create_ui()
        self.apply_theme()
        self.add_tab("https://duckduckgo.com")

    def load_json(self, filename, default):
        file = self.config_dir / filename
        if file.exists():
            try:
                return json.loads(file.read_text())
            except:
                pass
        return default

    def save_json(self, filename, data):
        (self.config_dir / filename).write_text(json.dumps(data, indent=2))

    def load_settings(self):
        return self.load_json("settings.json", {
            'ad_blocking': True, 
            'tracking_protection': True,
            'fingerprint_protection': True, 
            'webrtc_protection': True,
            'theme': 'dark', 
            'kill_switch': True,
            'vpn_protocol': 'openvpn'  # openvpn or wireguard
        })

    def save_settings(self):
        self.save_json("settings.json", self.settings)

    def load_privacy_filters(self):
        def load():
            try:
                print("Loading EasyList...")
                resp = requests.get("https://easylist.to/easylist/easylist.txt", timeout=30)
                self.filter_rules["ad"] = [
                    line.strip() for line in resp.text.splitlines() 
                    if line and not line.startswith('!') and not line.startswith('[')
                ]
                print(f"Loaded {len(self.filter_rules['ad'])} ad blocking rules")

                print("Loading EasyPrivacy...")
                resp = requests.get("https://easylist.to/easylist/easyprivacy.txt", timeout=30)
                self.filter_rules["track"] = [
                    line.strip() for line in resp.text.splitlines() 
                    if line and not line.startswith('!') and not line.startswith('[')
                ]
                print(f"Loaded {len(self.filter_rules['track'])} tracking protection rules")
            except Exception as e:
                print(f"Filter load failed: {e}")
        threading.Thread(target=load, daemon=True).start()

    def vpn_monitor(self):
        while True:
            self.vpn_connected = self.check_vpn()
            GLib.idle_add(self.update_vpn_ui)
            time.sleep(2)

    def check_vpn(self):
        """Check if VPN is connected by looking for TUN interface"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=5)
            return any('tun' in line.lower() and 'up' in line.lower() for line in result.stdout.splitlines())
        except:
            return False

    def connect_vpn(self, config_path, protocol=None):
        """Connect VPN using OpenVPN or WireGuard"""
        if self.vpn_connected:
            self.disconnect_vpn()
            return
        
        protocol = protocol or self.settings.get('vpn_protocol', 'openvpn')
        
        try:
            if protocol == "wireguard":
                if not os.path.exists(config_path):
                    print(f"WireGuard config not found: {config_path}")
                    return
                self.vpn_process = subprocess.Popen(
                    ["wg-quick", "up", config_path], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.PIPE
                )
            elif protocol == "openvpn":
                if not os.path.exists(config_path):
                    print(f"OpenVPN config not found: {config_path}")
                    return
                self.vpn_process = subprocess.Popen(
                    ["sudo", "openvpn", "--config", config_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
            
            time.sleep(3)  # Wait for connection
            
            if self.settings['kill_switch']:
                self.enable_kill_switch()
                
        except Exception as e:
            print(f"VPN connect failed: {e}")
            if self.vpn_process:
                self.vpn_process = None

    def disconnect_vpn(self):
        """Disconnect VPN"""
        if self.vpn_process:
            try:
                self.vpn_process.terminate()
                self.vpn_process.wait(timeout=5)
            except:
                self.vpn_process.kill()
            self.vpn_process = None
        
        # Disable kill switch
        if self.settings['kill_switch']:
            self.disable_kill_switch()

    def enable_kill_switch(self):
        """Enable kill switch - block all traffic if VPN disconnects"""
        try:
            # Allow loopback
            subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=False)
            # Allow VPN server IP (get from config)
            # Note: This is simplified - should parse VPN config for actual server IP
            subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "tun+", "-j", "ACCEPT"], check=False)
            # Drop everything else
            subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-j", "DROP"], check=False)
        except Exception as e:
            print(f"Kill switch enable failed: {e}")

    def disable_kill_switch(self):
        """Disable kill switch"""
        try:
            subprocess.run(["sudo", "iptables", "-D", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=False)
            subprocess.run(["sudo", "iptables", "-D", "OUTPUT", "-o", "tun+", "-j", "ACCEPT"], check=False)
            subprocess.run(["sudo", "iptables", "-D", "OUTPUT", "-j", "DROP"], check=False)
        except:
            pass

    def update_vpn_ui(self):
        """Update VPN status in UI"""
        if self.vpn_connected:
            self.vpn_status_label.set_text("🛡️ VPN: Connected")
            self.vpn_connect_btn.set_label("Disconnect VPN")
            for tab in self.tabs:
                tab['webview'].set_sensitive(True)
        else:
            self.vpn_status_label.set_text("⚠️ VPN: Disconnected - Browsing Blocked")
            self.vpn_connect_btn.set_label("Connect VPN")
            if self.settings.get('kill_switch'):
                for tab in self.tabs:
                    tab['webview'].load_html(self.vpn_warning_html(), "about:blank")
                    tab['webview'].set_sensitive(False)

    def vpn_warning_html(self):
        return """
        <html><body style="background: #1a1a1a; color: #fff; text-align: center; padding: 50px; font-family: sans-serif;">
        <h1 style="color: #ff6b6b;">🔒 VPN Required for Privacy</h1>
        <p style="font-size: 18px;">Connect your VPN to browse safely.</p>
        <p style="color: #888;">Your browsing is blocked until VPN is connected.</p>
        </body></html>
        """

    def create_ui(self):
        """Create the browser UI"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Toolbar
        toolbar = Gtk.Toolbar()
        
        new_tab_btn = Gtk.ToolButton(label="➕ New Tab")
        new_tab_btn.connect("clicked", lambda x: self.add_tab("https://duckduckgo.com"))
        toolbar.insert(new_tab_btn, -1)

        self.vpn_connect_btn = Gtk.ToolButton(label="Connect VPN")
        self.vpn_connect_btn.connect("clicked", self.on_vpn_toggle)
        toolbar.insert(self.vpn_connect_btn, -1)

        theme_btn = Gtk.ToolButton(label="🎨 Theme")
        theme_btn.connect("clicked", self.toggle_theme)
        toolbar.insert(theme_btn, -1)

        self.vpn_status_label = Gtk.Label(label="VPN: Checking...")
        toolitem = Gtk.ToolItem()
        toolitem.add(self.vpn_status_label)
        toolbar.insert(toolitem, -1)

        vbox.pack_start(toolbar, False, False, 0)

        # Notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        vbox.pack_start(self.notebook, True, True, 0)

        self.window.add(vbox)

        # CSS provider for theming
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), 
            self.css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def apply_theme(self):
        """Apply CSS theme"""
        if self.settings['theme'] == 'dark':
            css = """
            window { background: #1a1a1a; color: #fff; }
            label { color: #00ff00; }
            toolbar { background: #2d2d2d; }
            """
        else:
            css = """
            window { background: #fff; color: #000; }
            label { color: #00aa00; }
            toolbar { background: #f0f0f0; }
            """
        self.css_provider.load_from_data(css.encode())

    def toggle_theme(self, btn):
        """Toggle between dark and light theme"""
        self.settings['theme'] = 'light' if self.settings['theme'] == 'dark' else 'dark'
        self.save_settings()
        self.apply_theme()

    def on_vpn_toggle(self, btn):
        """Handle VPN connect/disconnect button"""
        if self.vpn_connected:
            self.disconnect_vpn()
        else:
            # Look for VPN configs
            config_paths = [
                self.config_dir / "vpn.conf",
                Path.home() / "Downloads" / "client.ovpn",
                Path.home() / ".config" / "openvpn" / "client.ovpn",
            ]
            
            config_path = None
            for path in config_paths:
                if path.exists():
                    config_path = str(path)
                    break
            
            if not config_path:
                print("No VPN config found. Please download from web portal.")
                dialog = Gtk.MessageDialog(
                    self.window,
                    Gtk.DialogFlags.MODAL,
                    Gtk.MessageType.INFO,
                    Gtk.ButtonsType.OK,
                    "VPN Config Required"
                )
                dialog.format_secondary_text("Please download a VPN config from the web portal first.")
                dialog.run()
                dialog.destroy()
                return
            
            protocol = 'openvpn' if config_path.endswith('.ovpn') else 'wireguard'
            self.connect_vpn(config_path, protocol)

    def add_tab(self, url):
        """Add a new browser tab"""
        scrolled = Gtk.ScrolledWindow()
        webview = WebKit2.WebView()
        
        # Configure WebView settings
        settings = webview.get_settings()
        settings.set_enable_plugins(False)
        settings.set_enable_javascript(True)
        settings.set_enable_developer_extras(True)

        # User content manager for script injection
        user_content = WebKit2.UserContentManager()
        
        if self.settings['fingerprint_protection']:
            js = self.anti_fingerprint_js()
            script = WebKit2.UserScript(
                js, 
                WebKit2.UserScriptInjectionTime.START, 
                WebKit2.UserContentInjectedFrames.ALL_FRAMES, 
                None, 
                None
            )
            user_content.add_script(script)
        
        webview.set_user_content_manager(user_content)

        # Connect signals for blocking
        webview.connect("decide-policy", self.on_decide_policy)
        webview.connect("resource-load-started", self.on_resource_load_started)

        webview.load_uri(url)
        scrolled.add(webview)

        # Tab label
        label = Gtk.Label(label=url[:30])
        self.notebook.append_page(scrolled, label)
        
        # Update label when page loads
        webview.connect("notify::uri", lambda w, p: label.set_text(w.get_uri()[:30]))
        
        self.tabs.append({'webview': webview, 'label': label})

    def on_decide_policy(self, webview, decision, decision_type):
        """Handle navigation policy decisions"""
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_request().get_uri()
            if self.is_blocked(uri):
                decision.ignore()
                return True
        return False

    def on_resource_load_started(self, webview, resource, request):
        """Handle resource loading - block ads/trackers"""
        uri = request.get_uri()
        if self.is_blocked(uri):
            request.cancel()

    def is_blocked(self, uri):
        """Check if URI should be blocked"""
        if not self.settings.get('ad_blocking', True) and not self.settings.get('tracking_protection', True):
            return False
        
        parsed = urlparse(uri)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Check ad blocking rules
        if self.settings.get('ad_blocking', True):
            for rule in self.filter_rules["ad"]:
                if rule and (rule in domain or domain.endswith('.' + rule) or rule in path):
                    return True
        
        # Check tracking protection rules
        if self.settings.get('tracking_protection', True):
            for rule in self.filter_rules["track"]:
                if rule and (rule in domain or domain.endswith('.' + rule) or rule in path):
                    return True
        
        return False

    def anti_fingerprint_js(self):
        """JavaScript to prevent fingerprinting"""
        return """
        (function() {
            // Disable canvas fingerprinting
            HTMLCanvasElement.prototype.getContext = function() { 
                return null; 
            };
            
            // Spoof screen resolution
            Object.defineProperty(screen, 'width', { value: 1920, writable: false });
            Object.defineProperty(screen, 'height', { value: 1080, writable: false });
            Object.defineProperty(screen, 'availWidth', { value: 1920, writable: false });
            Object.defineProperty(screen, 'availHeight', { value: 1040, writable: false });
            
            // Spoof timezone
            Date.prototype.getTimezoneOffset = function() { return -480; };
            
            // Disable WebGL fingerprinting
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.'; // UNMASKED_VENDOR_WEBGL
                if (parameter === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
                return null;
            };
        })();
        """

    def run(self):
        """Start the browser"""
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    app = PhazeBrowser()
    app.run()

