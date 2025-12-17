#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhazeBrowser: Secure VPN-Native Browser with Privacy Features
Custom GTK/WebKit2 browser with baked-in VPN, ad/tracking block, anti-fingerprinting.
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
        self.window = Gtk.Window(title="PhazeBrowser - Secure VPN Required")
        self.window.set_default_size(1200, 800)
        self.window.connect("destroy", Gtk.main_quit)

        self.vpn_connected = False
        self.config_dir = Path.home() / ".config" / "phazebrowser"
        self.config_dir.mkdir(exist_ok=True)
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
            'ad_blocking': True, 'tracking_protection': True,
            'fingerprint_protection': True, 'webrtc_protection': True,
            'theme': 'dark', 'kill_switch': True
        })

    def save_settings(self):
        self.save_json("settings.json", self.settings)

    def load_privacy_filters(self):
        def load():
            try:
                resp = requests.get("https://easylist.to/easylist/easylist.txt", timeout=10)
                self.filter_rules["ad"] = [line.strip() for line in resp.text.splitlines() if line and not line.startswith('!')]

                resp = requests.get("https://easylist.to/easylist/easyprivacy.txt", timeout=10)
                self.filter_rules["track"] = [line.strip() for line in resp.text.splitlines() if line and not line.startswith('!')]
            except Exception as e:
                print(f"Filter load failed: {e}")
        threading.Thread(target=load, daemon=True).start()

    def vpn_monitor(self):
        while True:
            self.vpn_connected = self.check_vpn()
            GLib.idle_add(self.update_vpn_ui)
            time.sleep(2)

    def check_vpn(self):
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=5)
            return any('tun' in line and 'state UP' in line for line in result.stdout.splitlines())
        except:
            return False

    def connect_vpn(self, config_path, protocol="wireguard"):
        if self.vpn_connected:
            return
        try:
            if protocol == "wireguard":
                subprocess.Popen(["wg-quick", "up", config_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            if self.settings['kill_switch']:
                self.enable_kill_switch()
        except Exception as e:
            print(f"VPN connect failed: {e}")

    def enable_kill_switch(self):
        try:
            subprocess.run(["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-d", "your_vpn_ip/32", "-j", "ACCEPT"], check=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-j", "DROP"], check=True)
        except:
            pass

    def update_vpn_ui(self):
        if self.vpn_connected:
            self.vpn_status_label.set_text("🛡️ VPN: Connected")
            self.vpn_connect_btn.set_label("Disconnect")
            for tab in self.tabs:
                tab['webview'].set_sensitive(True)
        else:
            self.vpn_status_label.set_text("⚠️ VPN: Disconnected - Browsing Blocked")
            self.vpn_connect_btn.set_label("Connect VPN")
            for tab in self.tabs:
                tab['webview'].load_html(self.vpn_warning_html(), "about:blank")
                tab['webview'].set_sensitive(False)

    def vpn_warning_html(self):
        return """
        <html><body style="background: #111; color: #fff; text-align: center; padding: 50px;">
        <h1>VPN Required for Privacy</h1>
        <p>Connect your VPN to browse safely.</p>
        </body></html>
        """

    def create_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        toolbar = Gtk.Toolbar()
        new_tab_btn = Gtk.ToolButton(label="New Tab")
        new_tab_btn.connect("clicked", lambda x: self.add_tab("https://duckduckgo.com"))
        toolbar.insert(new_tab_btn, -1)

        self.vpn_connect_btn = Gtk.ToolButton(label="Connect VPN")
        self.vpn_connect_btn.connect("clicked", self.on_vpn_toggle)
        toolbar.insert(self.vpn_connect_btn, -1)

        theme_btn = Gtk.ToolButton(label="Toggle Theme")
        theme_btn.connect("clicked", self.toggle_theme)
        toolbar.insert(theme_btn, -1)

        self.vpn_status_label = Gtk.Label(label="VPN: Checking...")
        toolitem = Gtk.ToolItem()
        toolitem.add(self.vpn_status_label)
        toolbar.insert(toolitem, -1)

        vbox.pack_start(toolbar, False, False, 0)

        self.notebook = Gtk.Notebook()
        vbox.pack_start(self.notebook, True, True, 0)

        self.window.add(vbox)

        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def apply_theme(self):
        css = """
        window { background: #1a1a1a; color: #fff; }
        label { color: #00ff00; }
        """ if self.settings['theme'] == 'dark' else """
        window { background: #fff; color: #000; }
        label { color: #00aa00; }
        """
        self.css_provider.load_from_data(css.encode())

    def toggle_theme(self, btn):
        self.settings['theme'] = 'light' if self.settings['theme'] == 'dark' else 'dark'
        self.save_settings()
        self.apply_theme()

    def on_vpn_toggle(self, btn):
        config = self.config_dir / "vpn.conf"
        if not config.exists():
            print("No VPN config—fetch from portal.")
            return
        self.connect_vpn(str(config))

    def add_tab(self, url):
        scrolled = Gtk.ScrolledWindow()
        webview = WebKit2.WebView()
        settings = webview.get_settings()
        settings.set_enable_plugins(False)

        user_content = WebKit2.UserContentManager()
        if self.settings['fingerprint_protection']:
            js = self.anti_fingerprint_js()
            script = WebKit2.UserScript(js, WebKit2.UserScriptInjectionTime.START, WebKit2.UserContentInjectedFrames.ALL_FRAMES, None, None)
            user_content.add_script(script)
        webview.set_user_content_manager(user_content)

        webview.connect("decide-policy", self.on_decide_policy)
        webview.connect("resource-load-started", self.on_resource_load_started)

        webview.load_uri(url)
        scrolled.add(webview)

        label = Gtk.Label(label="New Tab")
        self.notebook.append_page(scrolled, label)
        self.tabs.append({'webview': webview})

    def on_decide_policy(self, webview, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_request().get_uri()
            if self.is_blocked(uri):
                decision.ignore()
                return True
        return False

    def on_resource_load_started(self, webview, resource, request):
        uri = request.get_uri()
        if self.is_blocked(uri):
            request.cancel()

    def is_blocked(self, uri):
        parsed = urlparse(uri)
        domain = parsed.netloc.lower()
        for rule in self.filter_rules["ad"] + self.filter_rules["track"]:
            if rule in domain or domain in rule:
                return True
        return False

    def anti_fingerprint_js(self):
        return """
        (function() {
            HTMLCanvasElement.prototype.getContext = function() { return null; };
            Object.defineProperty(screen, 'width', { value: 1920 });
            Object.defineProperty(screen, 'height', { value: 1080 });
        })();
        """

    def run(self):
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    app = PhazeBrowser()
    app.run()

