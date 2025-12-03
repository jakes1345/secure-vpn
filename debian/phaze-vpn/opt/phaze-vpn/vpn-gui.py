#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhazeVPN Desktop Client
Simple GUI for connecting to PhazeVPN server
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
from pathlib import Path
import os
import math
import random
import time

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# VPS Configuration
VPS_URL = "https://phazevpn.com"
API_BASE = f"{VPS_URL}/api"

class PhazeVPNClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhazeVPN Client v1.1.0")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Session for maintaining cookies
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed certs
        
        # User info
        self.username = None
        self.role = None
        self.logged_in = False
        
        # Try to load icon
        self._load_icon()
        
        # Show splash screen first, then login
        self.show_splash_screen()
    
    def _load_icon(self):
        """Load application icon"""
        icon_paths = [
            Path(__file__).parent / "assets" / "icons" / "phazevpn.png",
            Path(__file__).parent / "phazevpn.png",
            Path("/opt/phaze-vpn/assets/icons/phazevpn.png"),
        ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    icon_img = tk.PhotoImage(file=str(icon_path))
                    self.root.iconphoto(True, icon_img)
                    self.root.icon_image = icon_img
                    break
                except Exception as e:
                    print(f"Could not load icon from {icon_path}: {e}")
    
    def show_splash_screen(self):
        """Show immersive animated splash screen with network phasing animation"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Set window to fullscreen-like (centered, large)
        self.root.geometry("900x700")
        self.root.configure(bg='#0a0a0a')  # Dark background
        
        # Create canvas for animation
        canvas = tk.Canvas(self.root, bg='#0a0a0a', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Load logo (try multiple paths)
        logo_paths = [
            Path(__file__).parent.parent / "web-portal" / "static" / "images" / "logo-optimized.png",
            Path(__file__).parent / "web-portal" / "static" / "images" / "logo-optimized.png",
            Path("/opt/phaze-vpn/web-portal/static/images/logo-optimized.png"),
            Path(__file__).parent / "assets" / "icons" / "phazevpn-512x512.png",
            Path(__file__).parent / "assets" / "icons" / "phazevpn.png",
        ]
        
        logo_img = None
        logo_width = 200
        logo_height = 200
        
        for logo_path in logo_paths:
            if logo_path.exists():
                try:
                    temp_img = tk.PhotoImage(file=str(logo_path))
                    # Get original dimensions
                    orig_width = temp_img.width()
                    orig_height = temp_img.height()
                    
                    # Calculate subsample to get desired size
                    if orig_width > logo_width:
                        x_subsample = orig_width // logo_width
                    else:
                        x_subsample = 1
                    if orig_height > logo_height:
                        y_subsample = orig_height // logo_height
                    else:
                        y_subsample = 1
                    
                    # Use the larger subsample to maintain aspect ratio
                    subsample = max(x_subsample, y_subsample, 1)
                    logo_img = temp_img.subsample(subsample, subsample)
                    break
                except Exception as e:
                    print(f"Could not load logo from {logo_path}: {e}")
                    continue
        
        # Network animation variables
        self.splash_canvas = canvas
        self.splash_nodes = []
        self.splash_connections = []
        self.splash_animation_running = True
        self.splash_logo_img = logo_img
        
        # Create network nodes - PHASING THROUGH effect
        num_nodes = 40  # More nodes for rich phasing effect
        canvas_width = canvas.winfo_width() or 900
        canvas_height = canvas.winfo_height() or 700
        for _ in range(num_nodes):
            # Create nodes at various depths (z-index) for 3D phasing effect
            node = {
                'x': random.uniform(30, canvas_width - 30),
                'y': random.uniform(30, canvas_height - 30),
                'z': random.uniform(0, 100),  # Depth: 0 = closest, 100 = farthest
                'vx': random.uniform(-2.0, 2.0),  # Faster movement
                'vy': random.uniform(-2.0, 2.0),
                'vz': random.uniform(0.5, 2.0),  # Moving toward viewer (phasing through)
                'radius': random.uniform(3, 6),
                'pulse': random.uniform(0, math.pi * 2),
                'pulse_speed': random.uniform(0.05, 0.15),
                'trail': [],  # Motion trail for phasing effect
            }
            self.splash_nodes.append(node)
        
        # Draw logo in center
        if logo_img:
            logo_x = 450
            logo_y = 200
            canvas.create_image(logo_x, logo_y, image=logo_img, anchor=tk.CENTER, tag='logo')
        
        # Title text
        canvas.create_text(450, 320, text="PhazeVPN", 
                         font=("Arial", 36, "bold"),
                         fill="#7b1fa2",  # Purple
                         tag='title')
        
        # Subtitle
        canvas.create_text(450, 370, text="Phazing Through Networks", 
                         font=("Arial", 14),
                         fill="#cddc39",  # Lime
                         tag='subtitle')
        
        # Loading text with animation
        self.splash_loading_text = canvas.create_text(450, 420, text="Connecting...", 
                                                      font=("Arial", 12),
                                                      fill="#888",
                                                      tag='loading')
        self.splash_loading_dots = 0
        self._animate_loading_text()
        
        # Start network animation
        self._animate_splash_network()
        
        # Auto-transition to login after 3 seconds
        self.root.after(3000, self._transition_to_login)
    
    def _animate_loading_text(self):
        """Animate loading text with dots"""
        if not self.splash_animation_running:
            return
        
        self.splash_loading_dots = (self.splash_loading_dots + 1) % 4
        dots = "." * self.splash_loading_dots
        self.splash_canvas.itemconfig(self.splash_loading_text, text=f"Connecting{dots}")
        
        self.root.after(500, self._animate_loading_text)
    
    def _animate_splash_network(self):
        """Animate PHASING THROUGH NETWORKS - we're moving through the network"""
        if not self.splash_animation_running:
            return
        
        canvas = self.splash_canvas
        canvas.delete('network')
        
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() or 900
        canvas_height = canvas.winfo_height() or 700
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Update and draw nodes - PHASING THROUGH effect
        for i, node in enumerate(self.splash_nodes):
            # Initialize missing properties (backwards compatibility)
            if 'z' not in node:
                node['z'] = random.uniform(0, 100)
            if 'vz' not in node:
                node['vz'] = random.uniform(0.5, 2.0)
            if 'trail' not in node:
                node['trail'] = []
            
            # Update position
            node['x'] += node['vx'] * 0.8
            node['y'] += node['vy'] * 0.8
            node['z'] -= node['vz']  # Move toward viewer (phasing through)
            node['pulse'] += node['pulse_speed']
            
            # PHASING THROUGH: When node passes through (z < 0), reset to back
            if node['z'] < 0:
                node['z'] = 100  # Reset to back
                node['x'] = random.uniform(30, canvas_width - 30)
                node['y'] = random.uniform(30, canvas_height - 30)
            
            # Wrap around edges (phasing through boundaries)
            margin = 30
            if node['x'] < margin:
                node['x'] = canvas_width - margin
            elif node['x'] > canvas_width - margin:
                node['x'] = margin
            if node['y'] < margin:
                node['y'] = canvas_height - margin
            elif node['y'] > canvas_height - margin:
                node['y'] = margin
            
            # Calculate depth-based size and position (3D phasing effect)
            # Closer nodes (lower z) are bigger and brighter
            depth_factor = 1.0 - (node['z'] / 100.0)  # 0 to 1 (0 = far, 1 = close)
            depth_scale = 0.3 + depth_factor * 1.5  # Scale from 0.3x to 1.8x
            
            # Perspective: closer nodes move toward center slightly
            perspective_x = node['x'] + (center_x - node['x']) * depth_factor * 0.1
            perspective_y = node['y'] + (center_y - node['y']) * depth_factor * 0.1
            
            # PHASING EFFECT: Phase in/out as we move through
            phase = (math.sin(node['pulse']) + 1) / 2
            phase_opacity = 0.4 + phase * 0.6
            phase_opacity *= (0.5 + depth_factor * 0.5)  # Closer = more visible
            
            # Size based on depth and phase
            pulse_factor = math.sin(node['pulse'] * 1.5) * 0.3 + 0.7
            node_radius = node['radius'] * depth_scale * pulse_factor
            
            # Color shifts as it phases (purple to cyan)
            phase_color = phase
            r = int(123 + (205 - 123) * phase_color * 0.5)
            g = int(31 + (220 - 31) * phase_color * 0.5)
            b = int(162 + (57 - 162) * phase_color * 0.5)
            
            # Apply phasing opacity
            r = int(r * phase_opacity)
            g = int(g * phase_opacity)
            b = int(b * phase_opacity)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Draw motion trail (phasing through effect)
            node['trail'].append((perspective_x, perspective_y, depth_factor))
            if len(node['trail']) > 5:
                node['trail'].pop(0)
            
            # Draw trail (shows movement through network)
            for j, (trail_x, trail_y, trail_depth) in enumerate(node['trail'][:-1]):
                trail_opacity = (j / len(node['trail'])) * phase_opacity * 0.3
                trail_radius = node_radius * trail_depth * 0.3
                trail_r = int(123 * trail_opacity)
                trail_g = int(31 * trail_opacity)
                trail_b = int(162 * trail_opacity)
                trail_color = f"#{trail_r:02x}{trail_g:02x}{trail_b:02x}"
                canvas.create_oval(
                    trail_x - trail_radius, trail_y - trail_radius,
                    trail_x + trail_radius, trail_y + trail_radius,
                    fill=trail_color, outline='', width=0, tag='network'
                )
            
            # Draw glow (phasing effect)
            glow_radius = node_radius * 1.8
            glow_opacity = phase_opacity * 0.4 * depth_factor
            glow_r = int(123 * glow_opacity)
            glow_g = int(31 * glow_opacity)
            glow_b = int(162 * glow_opacity)
            glow_color = f"#{glow_r:02x}{glow_g:02x}{glow_b:02x}"
            canvas.create_oval(
                perspective_x - glow_radius, perspective_y - glow_radius,
                perspective_x + glow_radius, perspective_y + glow_radius,
                fill=glow_color, outline='', width=0, tag='network'
            )
            
            # Main node
            canvas.create_oval(
                perspective_x - node_radius, perspective_y - node_radius,
                perspective_x + node_radius, perspective_y + node_radius,
                fill=color, outline='', width=0, tag='network'
            )
        
        # Draw PHASING connections - data flowing through network
        connection_distance = 150
        for i, node1 in enumerate(self.splash_nodes):
            for node2 in self.splash_nodes[i+1:]:
                # Use perspective positions
                depth1 = 1.0 - (node1['z'] / 100.0)
                depth2 = 1.0 - (node2['z'] / 100.0)
                center_x = canvas_width / 2
                center_y = canvas_height / 2
                
                x1 = node1['x'] + (center_x - node1['x']) * depth1 * 0.1
                y1 = node1['y'] + (center_y - node1['y']) * depth1 * 0.1
                x2 = node2['x'] + (center_x - node2['x']) * depth2 * 0.1
                y2 = node2['y'] + (center_y - node2['y']) * depth2 * 0.1
                
                dx = x2 - x1
                dy = y2 - y1
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < connection_distance:
                    # PHASING: Connection pulses as data phases through
                    phase1 = (math.sin(node1['pulse']) + 1) / 2
                    phase2 = (math.sin(node2['pulse']) + 1) / 2
                    connection_phase = (phase1 + phase2) / 2
                    
                    # Depth-based opacity (closer connections more visible)
                    avg_depth = (depth1 + depth2) / 2
                    base_opacity = 1.0 - (distance / connection_distance)
                    phase_pulse = math.sin(connection_phase * math.pi * 2) * 0.3 + 0.7
                    opacity = base_opacity * phase_pulse * 0.6 * (0.5 + avg_depth * 0.5)
                    opacity = max(0.2, min(0.9, opacity))
                    
                    # Purple connection with phasing gradient
                    r = int(123 * opacity)
                    g = int(31 * opacity)
                    b = int(162 * opacity)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Draw connection with phasing effect
                    line_width = 1 + connection_phase * 2.0
                    canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color, width=line_width, tag='network', smooth=True
                    )
                    
                    # Draw data packet phasing through connection
                    if connection_phase > 0.3:
                        # Animated packet moving along connection
                        packet_pos = (connection_phase - 0.3) / 0.7  # 0 to 1
                        packet_x = x1 + (x2 - x1) * packet_pos
                        packet_y = y1 + (y2 - y1) * packet_pos
                        packet_size = 4 + connection_phase * 3
                        packet_opacity = 0.7 + connection_phase * 0.3
                        packet_r = int(205 * packet_opacity)
                        packet_g = int(220 * packet_opacity)
                        packet_b = int(57 * packet_opacity)
                        packet_color = f"#{packet_r:02x}{packet_g:02x}{packet_b:02x}"
                        
                        # Packet glow
                        canvas.create_oval(
                            packet_x - packet_size * 1.5, packet_y - packet_size * 1.5,
                            packet_x + packet_size * 1.5, packet_y + packet_size * 1.5,
                            fill=packet_color, outline='', width=0, tag='network'
                        )
                        # Packet core
                        canvas.create_oval(
                            packet_x - packet_size, packet_y - packet_size,
                            packet_x + packet_size, packet_y + packet_size,
                            fill="#ffffff", outline='', width=0, tag='network'
                        )
        
        # Continue animation at smooth frame rate
        self.root.after(16, self._animate_splash_network)  # ~60 FPS for smooth phasing
    
    def _animate_login_network(self):
        """Animate professional network background for login screen - subtle and smooth"""
        if not self.login_animation_running or not self.login_canvas:
            return
        
        canvas = self.login_canvas
        
        # Clear previous frame
        canvas.delete('network')
        
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() or 900
        canvas_height = canvas.winfo_height() or 700
        
        # Update and draw nodes with professional smooth movement
        for node in self.login_nodes:
            # Smooth, slower movement
            node['x'] += node['vx'] * 0.7
            node['y'] += node['vy'] * 0.7
            node['pulse'] += node['pulse_speed'] * 0.5
            
            # PHASING: Wrap through edges (phasing through boundaries)
            margin = 30
            if node['x'] < margin:
                node['x'] = canvas_width - margin
            elif node['x'] > canvas_width - margin:
                node['x'] = margin
            if node['y'] < margin:
                node['y'] = canvas_height - margin
            elif node['y'] > canvas_height - margin:
                node['y'] = margin
            
            # PHASING EFFECT: Phase in/out
            phase = (math.sin(node['pulse']) + 1) / 2
            phase_opacity = 0.2 + phase * 0.4  # Subtle phasing for background
            
            # Size pulses
            pulse_factor = math.sin(node['pulse'] * 1.2) * 0.2 + 0.8
            node_radius = node['radius'] * pulse_factor
            
            # Color shifts as it phases
            phase_color = phase
            r = int(123 + (205 - 123) * phase_color * 0.3)
            g = int(31 + (220 - 31) * phase_color * 0.3)
            b = int(162 + (57 - 162) * phase_color * 0.3)
            
            # Apply phasing opacity
            r = int(r * phase_opacity)
            g = int(g * phase_opacity)
            b = int(b * phase_opacity)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Draw with subtle glow (phasing effect)
            glow_radius = node_radius * 1.3
            glow_opacity = phase_opacity * 0.2
            glow_r = int(123 * glow_opacity)
            glow_g = int(31 * glow_opacity)
            glow_b = int(162 * glow_opacity)
            glow_color = f"#{glow_r:02x}{glow_g:02x}{glow_b:02x}"
            canvas.create_oval(
                node['x'] - glow_radius, node['y'] - glow_radius,
                node['x'] + glow_radius, node['y'] + glow_radius,
                fill=glow_color, outline='', width=0, tag='network'
            )
            
            canvas.create_oval(
                node['x'] - node_radius, node['y'] - node_radius,
                node['x'] + node_radius, node['y'] + node_radius,
                fill=color, outline='', width=0, tag='network'
            )
        
        # Draw subtle connections (background effect)
        connection_distance = 100  # Shorter for cleaner look
        for i, node1 in enumerate(self.login_nodes):
            for node2 in self.login_nodes[i+1:]:
                dx = node2['x'] - node1['x']
                dy = node2['y'] - node1['y']
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < connection_distance:
                    # PHASING: Connection pulses as data phases through
                    phase1 = (math.sin(node1['pulse']) + 1) / 2
                    phase2 = (math.sin(node2['pulse']) + 1) / 2
                    connection_phase = (phase1 + phase2) / 2
                    
                    base_opacity = 1.0 - (distance / connection_distance)
                    phase_pulse = math.sin(connection_phase * math.pi * 2) * 0.2 + 0.8
                    opacity = base_opacity * phase_pulse * 0.3
                    opacity = max(0.1, min(0.3, opacity))
                    
                    r = int(123 * opacity)
                    g = int(31 * opacity)
                    b = int(162 * opacity)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Thinner lines for background
                    line_width = 0.5 + connection_phase * 0.5
                    canvas.create_line(
                        node1['x'], node1['y'],
                        node2['x'], node2['y'],
                        fill=color, width=line_width, tag='network', smooth=True
                    )
        
        # Continue animation at smooth frame rate
        self.root.after(16, self._animate_login_network)  # ~60 FPS
    
    def _animate_signup_network(self):
        """Animate network with PHASING effect for signup screen"""
        if not self.signup_animation_running or not self.signup_canvas:
            return
        
        canvas = self.signup_canvas
        canvas.delete('network')
        
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() or 900
        canvas_height = canvas.winfo_height() or 700
        
        # Update and draw nodes - PHASING THROUGH effect (same as login)
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        for node in self.signup_nodes:
            # Initialize missing properties (backwards compatibility)
            if 'z' not in node:
                node['z'] = random.uniform(0, 100)
            if 'vz' not in node:
                node['vz'] = random.uniform(0.3, 1.5)
            if 'trail' not in node:
                node['trail'] = []
            
            # Update position
            node['x'] += node['vx'] * 0.7
            node['y'] += node['vy'] * 0.7
            node['z'] -= node['vz']  # Move toward viewer (PHASING THROUGH)
            node['pulse'] += node['pulse_speed'] * 0.5
            
            # PHASING THROUGH: Reset when passes through
            if node['z'] < 0:
                node['z'] = 100
                node['x'] = random.uniform(30, canvas_width - 30)
                node['y'] = random.uniform(30, canvas_height - 30)
            
            # Wrap through edges
            margin = 30
            if node['x'] < margin:
                node['x'] = canvas_width - margin
            elif node['x'] > canvas_width - margin:
                node['x'] = margin
            if node['y'] < margin:
                node['y'] = canvas_height - margin
            elif node['y'] > canvas_height - margin:
                node['y'] = margin
            
            # Depth-based 3D effect
            depth_factor = 1.0 - (node['z'] / 100.0)
            depth_scale = 0.4 + depth_factor * 1.2
            
            # Perspective position
            perspective_x = node['x'] + (center_x - node['x']) * depth_factor * 0.08
            perspective_y = node['y'] + (center_y - node['y']) * depth_factor * 0.08
            
            # PHASING EFFECT
            phase = (math.sin(node['pulse']) + 1) / 2
            phase_opacity = 0.25 + phase * 0.45
            phase_opacity *= (0.4 + depth_factor * 0.6)
            
            pulse_factor = math.sin(node['pulse'] * 1.2) * 0.2 + 0.8
            node_radius = node['radius'] * depth_scale * pulse_factor
            
            # Color shifts
            phase_color = phase
            r = int(123 + (205 - 123) * phase_color * 0.4)
            g = int(31 + (220 - 31) * phase_color * 0.4)
            b = int(162 + (57 - 162) * phase_color * 0.4)
            
            r = int(r * phase_opacity)
            g = int(g * phase_opacity)
            b = int(b * phase_opacity)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Motion trail
            node['trail'].append((perspective_x, perspective_y, depth_factor))
            if len(node['trail']) > 4:
                node['trail'].pop(0)
            
            # Draw trail
            for j, (trail_x, trail_y, trail_depth) in enumerate(node['trail'][:-1]):
                trail_opacity = (j / len(node['trail'])) * phase_opacity * 0.25
                trail_radius = node_radius * trail_depth * 0.4
                trail_r = int(123 * trail_opacity)
                trail_g = int(31 * trail_opacity)
                trail_b = int(162 * trail_opacity)
                trail_color = f"#{trail_r:02x}{trail_g:02x}{trail_b:02x}"
                canvas.create_oval(
                    trail_x - trail_radius, trail_y - trail_radius,
                    trail_x + trail_radius, trail_y + trail_radius,
                    fill=trail_color, outline='', width=0, tag='network'
                )
            
            # Glow
            glow_radius = node_radius * 1.5
            glow_opacity = phase_opacity * 0.3 * depth_factor
            glow_r = int(123 * glow_opacity)
            glow_g = int(31 * glow_opacity)
            glow_b = int(162 * glow_opacity)
            glow_color = f"#{glow_r:02x}{glow_g:02x}{glow_b:02x}"
            canvas.create_oval(
                perspective_x - glow_radius, perspective_y - glow_radius,
                perspective_x + glow_radius, perspective_y + glow_radius,
                fill=glow_color, outline='', width=0, tag='network'
            )
            
            # Main node
            canvas.create_oval(
                perspective_x - node_radius, perspective_y - node_radius,
                perspective_x + node_radius, perspective_y + node_radius,
                fill=color, outline='', width=0, tag='network'
            )
        
        # Draw PHASING connections with data flow
        connection_distance = 120
        for i, node1 in enumerate(self.signup_nodes):
            for node2 in self.signup_nodes[i+1:]:
                # Use perspective positions
                depth1 = 1.0 - (node1.get('z', 50) / 100.0)
                depth2 = 1.0 - (node2.get('z', 50) / 100.0)
                
                x1 = node1['x'] + (center_x - node1['x']) * depth1 * 0.08
                y1 = node1['y'] + (center_y - node1['y']) * depth1 * 0.08
                x2 = node2['x'] + (center_x - node2['x']) * depth2 * 0.08
                y2 = node2['y'] + (center_y - node2['y']) * depth2 * 0.08
                
                dx = x2 - x1
                dy = y2 - y1
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < connection_distance:
                    # PHASING: Data flowing through
                    phase1 = (math.sin(node1['pulse']) + 1) / 2
                    phase2 = (math.sin(node2['pulse']) + 1) / 2
                    connection_phase = (phase1 + phase2) / 2
                    
                    avg_depth = (depth1 + depth2) / 2
                    base_opacity = 1.0 - (distance / connection_distance)
                    phase_pulse = math.sin(connection_phase * math.pi * 2) * 0.25 + 0.75
                    opacity = base_opacity * phase_pulse * 0.35 * (0.3 + avg_depth * 0.7)
                    opacity = max(0.12, min(0.4, opacity))
                    
                    r = int(123 * opacity)
                    g = int(31 * opacity)
                    b = int(162 * opacity)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    line_width = 0.6 + connection_phase * 0.8
                    canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color, width=line_width, tag='network', smooth=True
                    )
                    
                    # Data packet phasing through
                    if connection_phase > 0.4:
                        packet_pos = (connection_phase - 0.4) / 0.6
                        packet_x = x1 + (x2 - x1) * packet_pos
                        packet_y = y1 + (y2 - y1) * packet_pos
                        packet_size = 2.5 + connection_phase * 2
                        packet_color = f"#{205:02x}{220:02x}{57:02x}"
                        canvas.create_oval(
                            packet_x - packet_size, packet_y - packet_size,
                            packet_x + packet_size, packet_y + packet_size,
                            fill=packet_color, outline='', width=0, tag='network'
                        )
        
        # Continue animation
        self.root.after(16, self._animate_signup_network)  # ~60 FPS
    
    def _transition_to_login(self):
        """Transition from splash to login"""
        self.splash_animation_running = False
        self.splash_canvas = None
        self.splash_nodes = None
        # Smooth transition to login (keep animation running)
        self.root.after(100, self.show_login)  # Small delay for smooth transition
    
    def show_login(self):
        """Show login window with simple dark background"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Stop any running animations
        self.login_animation_running = False
        self.splash_animation_running = False
        
        # Set dark background (no animation)
        self.root.configure(bg='#1a1a1a')
        
        # Create main frame with dark background
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Login frame (centered)
        login_frame = tk.Frame(main_frame, bg='#1a1a1a', padx=40, pady=40)
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title (with color)
        title_label = tk.Label(login_frame, text="PhazeVPN", 
                              font=("Arial", 24, "bold"),
                              bg='#1a1a1a', fg='#7b1fa2')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(login_frame, text="Secure VPN Connection", 
                                 font=("Arial", 12),
                                 bg='#1a1a1a', fg='#cddc39')
        subtitle_label.pack(pady=5)
        
        # Status label
        self.status_label = tk.Label(login_frame, text="", 
                                    bg='#1a1a1a', fg='#ff0000',
                                    font=("Arial", 10))
        self.status_label.pack(pady=5)
        
        # Username
        username_label = tk.Label(login_frame, text="Username:", 
                                 bg='#1a1a1a', fg='#ffffff',
                                 font=("Arial", 10))
        username_label.pack(anchor=tk.W, pady=(20, 5))
        self.username_entry = tk.Entry(login_frame, width=32, 
                                      bg='#2a2a2a', fg='#ffffff',
                                      insertbackground='#ffffff',
                                      relief=tk.FLAT, bd=5)
        self.username_entry.pack(pady=5)
        self.username_entry.focus()
        
        # Password
        password_label = tk.Label(login_frame, text="Password:", 
                                 bg='#1a1a1a', fg='#ffffff',
                                 font=("Arial", 10))
        password_label.pack(anchor=tk.W, pady=(10, 5))
        self.password_entry = tk.Entry(login_frame, width=32, show="*",
                                      bg='#2a2a2a', fg='#ffffff',
                                      insertbackground='#ffffff',
                                      relief=tk.FLAT, bd=5)
        self.password_entry.pack(pady=5)
        self.password_entry.bind('<Return>', lambda e: self.do_login())
        
        # Buttons frame
        buttons_frame = tk.Frame(login_frame, bg='#1a1a1a')
        buttons_frame.pack(pady=20)
        
        # Login button (styled)
        login_btn = tk.Button(buttons_frame, text="Login", 
                            command=self.do_login, width=22,
                            bg='#7b1fa2', fg='#ffffff',
                            font=("Arial", 11, "bold"),
                            relief=tk.FLAT, bd=0, padx=10, pady=8,
                            cursor='hand2',
                            activebackground='#9c27b0',
                            activeforeground='#ffffff')
        login_btn.pack(pady=5)
        
        # Signup button (styled)
        signup_btn = tk.Button(buttons_frame, text="Create Account", 
                              command=self.show_signup, width=22,
                              bg='#cddc39', fg='#0a0a0a',
                              font=("Arial", 11, "bold"),
                              relief=tk.FLAT, bd=0, padx=10, pady=8,
                              cursor='hand2',
                              activebackground='#d4e157',
                              activeforeground='#0a0a0a')
        signup_btn.pack(pady=5)
        
        # Status label
        self.status_label = tk.Label(login_frame, text="", 
                                    bg='#0a0a0a', fg='#ff4444',
                                    font=("Arial", 9))
        self.status_label.pack(pady=10)
        
        # Info label
        info_label = tk.Label(login_frame, 
                              text="Or sign up at phazevpn.com",
                              font=("Arial", 9),
                              bg='#0a0a0a', fg='#888888')
        info_label.pack(pady=5)
    
    def do_login(self):
        """Handle login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.status_label.config(text="Please enter username and password")
            return
        
        self.status_label.config(text="Logging in...", fg="blue")
        self.root.update()
        
        # Login in background thread
        threading.Thread(target=self._login_thread, args=(username, password), daemon=True).start()
    
    def _login_thread(self, username, password):
        """Login thread"""
        try:
            response = self.session.post(
                f"{API_BASE}/app/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.username = username
                    self.role = data.get('user', {}).get('role', 'user')
                    self.logged_in = True
                    self.root.after(0, self.show_dashboard)
                else:
                    error = data.get('error', 'Login failed')
                    self.root.after(0, lambda: self.status_label.config(text=error, fg="red"))
            else:
                error = "Invalid username or password"
                if response.status_code == 401:
                    try:
                        data = response.json()
                        error = data.get('error', error)
                    except:
                        pass
                self.root.after(0, lambda: self.status_label.config(text=error, fg="red"))
        except requests.exceptions.RequestException as e:
            error = f"Connection error: {str(e)}"
            self.root.after(0, lambda: self.status_label.config(text=error, fg="red"))
    
    def show_signup(self):
        """Show signup window with animated network background"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Set dark background
        self.root.configure(bg='#0a0a0a')
        
        # Create canvas for animated background
        canvas = tk.Canvas(self.root, bg='#0a0a0a', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize network animation for signup screen
        self.signup_canvas = canvas
        self.signup_nodes = []
        self.signup_animation_running = True
        
        # Create network nodes (same style as login)
        num_nodes = 25
        canvas_width = canvas.winfo_width() or 900
        canvas_height = canvas.winfo_height() or 700
        for _ in range(num_nodes):
            node = {
                'x': random.uniform(30, canvas_width - 30),
                'y': random.uniform(30, canvas_height - 30),
                'vx': random.uniform(-0.8, 0.8),
                'vy': random.uniform(-0.8, 0.8),
                'radius': random.uniform(2, 4),
                'pulse': random.uniform(0, math.pi * 2),
                'pulse_speed': random.uniform(0.03, 0.08),
            }
            self.signup_nodes.append(node)
        
        # Start background animation
        self._animate_signup_network()
        
        # Create semi-transparent overlay frame for signup content
        overlay_frame = tk.Frame(canvas, bg='#0a0a0a', bd=0)
        overlay_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=400, height=550)
        
        # Signup frame
        signup_frame = ttk.Frame(overlay_frame, padding="20")
        signup_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(signup_frame, text="Create Account", 
                              font=("Arial", 24, "bold"),
                              bg='#0a0a0a', fg='#7b1fa2')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(signup_frame, text="Sign up for PhazeVPN", 
                                 font=("Arial", 12),
                                 bg='#0a0a0a', fg='#cddc39')
        subtitle_label.pack(pady=5)
        
        # Username
        username_label = tk.Label(signup_frame, text="Username:", 
                                  bg='#0a0a0a', fg='#ffffff',
                                  font=("Arial", 10))
        username_label.pack(anchor=tk.W, pady=(20, 5))
        self.signup_username_entry = tk.Entry(signup_frame, width=32,
                                              bg='#1a1a1a', fg='#ffffff',
                                              insertbackground='#ffffff',
                                              relief=tk.FLAT, bd=5)
        self.signup_username_entry.pack(pady=5)
        self.signup_username_entry.focus()
        
        # Email
        email_label = tk.Label(signup_frame, text="Email:", 
                              bg='#0a0a0a', fg='#ffffff',
                              font=("Arial", 10))
        email_label.pack(anchor=tk.W, pady=(10, 5))
        self.signup_email_entry = tk.Entry(signup_frame, width=32,
                                           bg='#1a1a1a', fg='#ffffff',
                                           insertbackground='#ffffff',
                                           relief=tk.FLAT, bd=5)
        self.signup_email_entry.pack(pady=5)
        
        # Password
        password_label = tk.Label(signup_frame, text="Password:", 
                                  bg='#0a0a0a', fg='#ffffff',
                                  font=("Arial", 10))
        password_label.pack(anchor=tk.W, pady=(10, 5))
        self.signup_password_entry = tk.Entry(signup_frame, width=32, show="*",
                                             bg='#1a1a1a', fg='#ffffff',
                                             insertbackground='#ffffff',
                                             relief=tk.FLAT, bd=5)
        self.signup_password_entry.pack(pady=5)
        
        # Confirm Password
        confirm_label = tk.Label(signup_frame, text="Confirm Password:", 
                                bg='#0a0a0a', fg='#ffffff',
                                font=("Arial", 10))
        confirm_label.pack(anchor=tk.W, pady=(10, 5))
        self.signup_confirm_entry = tk.Entry(signup_frame, width=32, show="*",
                                             bg='#1a1a1a', fg='#ffffff',
                                             insertbackground='#ffffff',
                                             relief=tk.FLAT, bd=5)
        self.signup_confirm_entry.pack(pady=5)
        
        # Signup button
        signup_btn = tk.Button(signup_frame, text="Create Account", 
                              command=self.do_signup, width=22,
                              bg='#cddc39', fg='#0a0a0a',
                              font=("Arial", 11, "bold"),
                              relief=tk.FLAT, bd=0, padx=10, pady=8,
                              cursor='hand2',
                              activebackground='#d4e157',
                              activeforeground='#0a0a0a')
        signup_btn.pack(pady=20)
        
        # Back to login
        back_btn = tk.Button(signup_frame, text="Back to Login", 
                            command=self.show_login, width=22,
                            bg='#333333', fg='#ffffff',
                            font=("Arial", 10),
                            relief=tk.FLAT, bd=0, padx=10, pady=6,
                            cursor='hand2',
                            activebackground='#444444',
                            activeforeground='#ffffff')
        back_btn.pack(pady=5)
        
        # Status label
        self.signup_status_label = tk.Label(signup_frame, text="", 
                                           bg='#0a0a0a', fg='#ff4444',
                                           font=("Arial", 9))
        self.signup_status_label.pack(pady=10)
    
    def do_signup(self):
        """Handle signup"""
        username = self.signup_username_entry.get().strip()
        email = self.signup_email_entry.get().strip()
        password = self.signup_password_entry.get()
        confirm = self.signup_confirm_entry.get()
        
        if not username or not email or not password:
            self.signup_status_label.config(text="Please fill in all fields")
            return
        
        if password != confirm:
            self.signup_status_label.config(text="Passwords do not match")
            return
        
        if len(password) < 6:
            self.signup_status_label.config(text="Password must be at least 6 characters")
            return
        
        self.signup_status_label.config(text="Creating account...", fg="blue")
        self.root.update()
        
        # Signup in background thread
        threading.Thread(target=self._signup_thread, args=(username, email, password), daemon=True).start()
    
    def _signup_thread(self, username, email, password):
        """Signup thread"""
        try:
            response = self.session.post(
                f"{API_BASE}/app/signup",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "confirm_password": password  # API expects this field
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.root.after(0, lambda: self.signup_status_label.config(
                        text="Account created! You can now login.", fg="green"
                    ))
                    # Auto-switch to login after 2 seconds
                    self.root.after(2000, self.show_login)
                else:
                    error = data.get('error', 'Signup failed')
                    self.root.after(0, lambda: self.signup_status_label.config(text=error, fg="red"))
            else:
                error = "Signup failed"
                if response.status_code == 400:
                    try:
                        data = response.json()
                        error = data.get('error', error)
                    except:
                        pass
                self.root.after(0, lambda: self.signup_status_label.config(text=error, fg="red"))
        except requests.exceptions.RequestException as e:
            error = f"Connection error: {str(e)}"
            self.root.after(0, lambda: self.signup_status_label.config(text=error, fg="red"))
    
    def show_dashboard(self):
        """Show main dashboard with animated background"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Stop splash animation only
        self.splash_animation_running = False
        
        # Set dark background
        self.root.configure(bg='#0a0a0a')
        
        # Create canvas for animated background
        canvas = tk.Canvas(self.root, bg='#0a0a0a', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize network animation for dashboard
        self.dashboard_canvas = canvas
        self.dashboard_nodes = []
        self.dashboard_animation_running = True
        
        # Create network nodes (subtle background animation)
        num_nodes = 20  # Fewer for dashboard (less distracting)
        canvas_width = canvas.winfo_width() or 900
        canvas_height = canvas.winfo_height() or 700
        for _ in range(num_nodes):
            node = {
                'x': random.uniform(30, canvas_width - 30),
                'y': random.uniform(30, canvas_height - 30),
                'vx': random.uniform(-0.5, 0.5),  # Very slow for background
                'vy': random.uniform(-0.5, 0.5),
                'radius': random.uniform(1.5, 3),  # Smaller nodes
                'pulse': random.uniform(0, math.pi * 2),
                'pulse_speed': random.uniform(0.02, 0.05),  # Very slow pulse
            }
            self.dashboard_nodes.append(node)
        
        # Start background animation
        self._animate_dashboard_network()
        
        # Create semi-transparent overlay for dashboard content
        overlay_frame = tk.Frame(canvas, bg='#0a0a0a', bd=0)
        overlay_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Main frame (on top of animation)
        main_frame = tk.Frame(overlay_frame, bg='#1a1a1a', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#1a1a1a')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="PhazeVPN Dashboard", 
                              font=("Arial", 18, "bold"),
                              bg='#1a1a1a', fg='#7b1fa2')
        title_label.pack(side=tk.LEFT)
        
        user_label = tk.Label(header_frame, text=f"Logged in as: {self.username} ({self.role})", 
                             font=("Arial", 10),
                             bg='#1a1a1a', fg='#ffffff')
        user_label.pack(side=tk.RIGHT)
        
        logout_btn = tk.Button(header_frame, text="Logout", command=self.logout, width=10,
                              bg='#7b1fa2', fg='#ffffff', relief=tk.FLAT)
        logout_btn.pack(side=tk.RIGHT, padx=10)
        
        # Configs section
        configs_frame = tk.LabelFrame(main_frame, text="Your VPN Configurations", 
                                     bg='#1a1a1a', fg='#ffffff',
                                     padx=10, pady=10)
        configs_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configs list
        list_frame = tk.Frame(configs_frame, bg='#1a1a1a')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame, bg='#2a2a2a')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.configs_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                          bg='#2a2a2a', fg='#ffffff',
                                          selectbackground='#7b1fa2')
        self.configs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.configs_listbox.yview)
        
        # Buttons frame
        buttons_frame = tk.Frame(configs_frame, bg='#1a1a1a')
        buttons_frame.pack(fill=tk.X, pady=10)
        
        download_btn = tk.Button(buttons_frame, text="Download Config", command=self.download_config, width=20,
                                bg='#7b1fa2', fg='#ffffff', relief=tk.FLAT)
        download_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(buttons_frame, text="Refresh", command=self.refresh_configs, width=15,
                               bg='#cddc39', fg='#1a1a1a', relief=tk.FLAT)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        debug_btn = tk.Button(buttons_frame, text="Debug Info", command=self.show_debug_info, width=15,
                             bg='#2a2a2a', fg='#ffffff', relief=tk.FLAT)
        debug_btn.pack(side=tk.LEFT, padx=5)
        
        if self.role in ['admin', 'moderator']:
            add_client_btn = tk.Button(buttons_frame, text="Add Client", command=self.add_client, width=15,
                                      bg='#cddc39', fg='#1a1a1a', relief=tk.FLAT)
            add_client_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.dashboard_status = tk.Label(main_frame, text="", 
                                        bg='#1a1a1a', fg='#00ff00',
                                        font=("Arial", 10))
        self.dashboard_status.pack(pady=5)
        
        # Load configs
        self.refresh_configs()
    
    def _animate_dashboard_network(self):
        """Animate subtle PHASING network background for dashboard"""
        if not self.dashboard_animation_running or not self.dashboard_canvas:
            return
        
        canvas = self.dashboard_canvas
        canvas.delete('network')
        
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() or 900
        canvas_height = canvas.winfo_height() or 700
        
        # Update and draw nodes with subtle PHASING
        for node in self.dashboard_nodes:
            # Very slow movement
            node['x'] += node['vx'] * 0.5
            node['y'] += node['vy'] * 0.5
            node['pulse'] += node['pulse_speed'] * 0.4
            
            # PHASING: Wrap through edges (very subtle)
            margin = 30
            if node['x'] < margin:
                node['x'] = canvas_width - margin
            elif node['x'] > canvas_width - margin:
                node['x'] = margin
            if node['y'] < margin:
                node['y'] = canvas_height - margin
            elif node['y'] > canvas_height - margin:
                node['y'] = margin
            
            # Very subtle PHASING effect
            phase = (math.sin(node['pulse']) + 1) / 2
            phase_opacity = 0.1 + phase * 0.15  # Very subtle for background
            
            pulse_factor = math.sin(node['pulse'] * 0.8) * 0.15 + 0.85
            node_radius = node['radius'] * pulse_factor
            
            # Very subtle color shift
            phase_color = phase
            r = int(123 + (205 - 123) * phase_color * 0.1)
            g = int(31 + (220 - 31) * phase_color * 0.1)
            b = int(162 + (57 - 162) * phase_color * 0.1)
            
            r = int(r * phase_opacity)
            g = int(g * phase_opacity)
            b = int(b * phase_opacity)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Very subtle nodes
            canvas.create_oval(
                node['x'] - node_radius, node['y'] - node_radius,
                node['x'] + node_radius, node['y'] + node_radius,
                fill=color, outline='', width=0, tag='network'
            )
        
        # Draw very subtle PHASING connections
        connection_distance = 80
        for i, node1 in enumerate(self.dashboard_nodes):
            for node2 in self.dashboard_nodes[i+1:]:
                dx = node2['x'] - node1['x']
                dy = node2['y'] - node1['y']
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < connection_distance:
                    # Subtle phasing
                    phase1 = (math.sin(node1['pulse']) + 1) / 2
                    phase2 = (math.sin(node2['pulse']) + 1) / 2
                    connection_phase = (phase1 + phase2) / 2
                    
                    base_opacity = 1.0 - (distance / connection_distance)
                    phase_pulse = math.sin(connection_phase * math.pi * 2) * 0.1 + 0.9
                    opacity = base_opacity * phase_pulse * 0.15
                    opacity = max(0.05, min(0.2, opacity))
                    
                    r = int(123 * opacity)
                    g = int(31 * opacity)
                    b = int(162 * opacity)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Very thin lines
                    canvas.create_line(
                        node1['x'], node1['y'],
                        node2['x'], node2['y'],
                        fill=color, width=0.3, tag='network', smooth=True
                    )
        
        # Continue animation
        self.root.after(20, self._animate_dashboard_network)  # ~50 FPS
    
    def refresh_configs(self):
        """Refresh list of configs"""
        self.configs_listbox.delete(0, tk.END)
        self.dashboard_status.config(text="Loading configs...", fg='#0088ff')
        self.root.update()
        
        threading.Thread(target=self._refresh_configs_thread, daemon=True).start()
    
    def _refresh_configs_thread(self):
        """Refresh configs in background"""
        try:
            # Try /api/my-clients first (more reliable)
            response = self.session.get(f"{API_BASE}/my-clients", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    clients = data.get('clients', [])
                    # Handle both dict and string formats
                    config_names = []
                    for c in clients:
                        if isinstance(c, dict):
                            name = c.get('name') or c.get('vpn_config') or ''
                            if name:
                                config_names.append(name)
                        else:
                            name = str(c).strip()
                            if name:
                                config_names.append(name)
                    # Filter out empty names
                    config_names = [name for name in config_names if name]
                    
                    self.root.after(0, lambda: self._update_configs_list(config_names))
                    if len(config_names) > 0:
                        self.root.after(0, lambda: self.dashboard_status.config(
                            text=f"Found {len(config_names)} configuration(s): {', '.join(config_names)}", fg="green"))
                    else:
                        # Debug: show what we got
                        sub_info = data.get('subscription', {})
                        debug_msg = f"API returned {len(clients)} clients but no valid names. Raw data: {clients[:3]}"
                        self.root.after(0, lambda: self.dashboard_status.config(
                            text=f"No configs found. API returned {len(clients)} clients. Click Debug Info for details.", fg="orange"))
                    return
            elif response.status_code == 401:
                self.root.after(0, lambda: self.dashboard_status.config(
                    text="Session expired. Please log in again.", fg="red"))
                self.root.after(2000, self.logout)
                return
            
            # Fallback to /api/app/configs
            response = self.session.get(f"{API_BASE}/app/configs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    configs = data.get('configs', [])
                    config_names = [cfg['name'] for cfg in configs]
                    self.root.after(0, lambda: self._update_configs_list(config_names))
                    if len(config_names) > 0:
                        self.root.after(0, lambda: self.dashboard_status.config(
                            text=f"Found {len(config_names)} configuration(s): {', '.join(config_names)}", fg="green"))
                    else:
                        self.root.after(0, lambda: self.dashboard_status.config(
                            text="No configurations found. Add a client to get started.", fg="orange"))
                else:
                    error = data.get('error', 'Failed to load configs')
                    self.root.after(0, lambda: self.dashboard_status.config(
                        text=f"Error: {error}", fg="red"))
            elif response.status_code == 401:
                self.root.after(0, lambda: self.dashboard_status.config(
                    text="Session expired. Please log in again.", fg="red"))
                self.root.after(2000, self.logout)
            else:
                error_text = f"Error {response.status_code}"
                try:
                    error_data = response.json()
                    error_text = error_data.get('error', error_text)
                except:
                    error_text = response.text[:50] if response.text else error_text
                self.root.after(0, lambda: self.dashboard_status.config(
                    text=f"Error: {error_text}", fg="red"))
        except Exception as e:
            self.root.after(0, lambda: self.dashboard_status.config(
                text=f"Connection error: {str(e)}", fg="red"))
    
    def _update_configs_list(self, config_names):
        """Update configs listbox"""
        self.configs_listbox.delete(0, tk.END)
        for name in config_names:
            self.configs_listbox.insert(tk.END, name)
    
    def download_config(self):
        """Download selected config"""
        selection = self.configs_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a configuration to download")
            return
        
        client_name = self.configs_listbox.get(selection[0])
        
        # Ask for config type
        config_type = self._ask_config_type()
        if not config_type:
            return
        
        self.dashboard_status.config(text=f"Downloading {client_name} ({config_type})...", fg="blue")
        self.root.update()
        
        threading.Thread(target=self._download_thread, args=(client_name, config_type), daemon=True).start()
    
    def _ask_config_type(self):
        """Ask user for config type"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Config Type")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        result = [None]
        
        ttk.Label(dialog, text="Select configuration type:", font=("Arial", 11, "bold")).pack(pady=10)
        
        # Info label - emphasize security
        info_label = tk.Label(dialog, 
                              text="🔒 Recommended: Audited protocols",
                              font=("Arial", 9, "bold"),
                              fg="green")
        info_label.pack(pady=5)
        
        security_label = tk.Label(dialog, 
                                  text="OpenVPN (audited) • WireGuard (modern, audited)",
                                  font=("Arial", 8),
                                  fg="gray")
        security_label.pack()
        
        # Certificate info
        cert_info = tk.Label(dialog, 
                             text="✨ All protocols use modern Ed25519 certificates",
                             font=("Arial", 7),
                             fg="blue")
        cert_info.pack(pady=2)
        
        type_frame = ttk.Frame(dialog)
        type_frame.pack(pady=10)
        
        def select_type(cfg_type):
            result[0] = cfg_type
            dialog.destroy()
        
        # OpenVPN - Recommended
        openvpn_btn = ttk.Button(type_frame, text="OpenVPN\n(Recommended)", 
                                 command=lambda: select_type("openvpn"), width=18)
        openvpn_btn.pack(side=tk.LEFT, padx=5)
        
        # WireGuard - Recommended
        wireguard_btn = ttk.Button(type_frame, text="WireGuard\n(Modern)", 
                                  command=lambda: select_type("wireguard"), width=18)
        wireguard_btn.pack(side=tk.LEFT, padx=5)
        
        # PhazeVPN - Experimental (security warning)
        phazevpn_frame = tk.Frame(dialog)
        phazevpn_frame.pack(pady=5)
        
        # Warning label
        warning_label = tk.Label(phazevpn_frame, 
                 text="⚠️ EXPERIMENTAL: PhazeVPN Protocol (Not Audited)", 
                 font=("Arial", 8, "bold"), 
                 fg="red",
                 bg=dialog.cget('bg'))
        warning_label.pack()
        
        # Details
        details_label = tk.Label(phazevpn_frame, 
                 text="• Custom protocol - not tested by security auditors", 
                 font=("Arial", 7), 
                 fg="orange",
                 bg=dialog.cget('bg'))
        details_label.pack()
        
        details2_label = tk.Label(phazevpn_frame, 
                 text="• Uses ChaCha20-Poly1305 encryption (modern & fast)", 
                 font=("Arial", 7), 
                 fg="gray",
                 bg=dialog.cget('bg'))
        details2_label.pack()
        
        details3_label = tk.Label(phazevpn_frame, 
                 text="• For production use, choose OpenVPN or WireGuard", 
                 font=("Arial", 7, "italic"), 
                 fg="gray",
                 bg=dialog.cget('bg'))
        details3_label.pack()
        
        # Button with confirmation
        def confirm_phazevpn():
            confirm = messagebox.askyesno(
                "Experimental Protocol Warning",
                "⚠️ PhazeVPN Protocol is EXPERIMENTAL and not audited.\n\n"
                "This protocol:\n"
                "• Has NOT been tested by security researchers\n"
                "• May have undiscovered vulnerabilities\n"
                "• Is for testing purposes only\n\n"
                "For production use, please use OpenVPN or WireGuard.\n\n"
                "Do you want to continue with PhazeVPN Protocol?",
                icon="warning"
            )
            if confirm:
                select_type("phazevpn")
        
        phazevpn_btn = ttk.Button(phazevpn_frame, 
                                 text="PhazeVPN Protocol\n(Experimental)", 
                                 command=confirm_phazevpn, 
                                 width=20)
        phazevpn_btn.pack(pady=5)
        
        dialog.wait_window()
        return result[0]
    
    def _download_thread(self, client_name, config_type):
        """Download config in background"""
        try:
            url = f"{VPS_URL}/download/{client_name}?type={config_type}"
            response = self.session.get(url, timeout=30, stream=True)
            
            if response.status_code == 200:
                # Ask where to save
                filename = f"{client_name}_{config_type}.conf"
                if config_type == "openvpn":
                    filename = f"{client_name}.ovpn"
                elif config_type == "wireguard":
                    filename = f"{client_name}.conf"
                elif config_type == "phazevpn":
                    filename = f"{client_name}_phazevpn.conf"
                
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".conf",
                    filetypes=[("Config files", "*.conf *.ovpn"), ("All files", "*.*")],
                    initialfile=filename
                )
                
                if save_path:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    self.root.after(0, lambda: self.dashboard_status.config(
                        text=f"✅ Config saved to {save_path}", fg="green"))
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Configuration saved to:\n{save_path}"))
                else:
                    self.root.after(0, lambda: self.dashboard_status.config(
                        text="Download cancelled", fg="gray"))
            else:
                error = f"Failed to download: {response.status_code}"
                self.root.after(0, lambda: self.dashboard_status.config(text=error, fg="red"))
        except Exception as e:
            self.root.after(0, lambda: self.dashboard_status.config(
                text=f"Error: {str(e)}", fg="red"))
    
    def add_client(self):
        """Add new client (admin/moderator only)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Client")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Client Name:", font=("Arial", 10)).pack(pady=10)
        
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        status_label = ttk.Label(dialog, text="", fg="red")
        status_label.pack(pady=5)
        
        def do_add():
            client_name = name_entry.get().strip()
            if not client_name:
                status_label.config(text="Please enter a client name")
                return
            
            if not client_name.replace('_', '').replace('-', '').isalnum():
                status_label.config(text="Client name must be alphanumeric (with _ or -)")
                return
            
            status_label.config(text="Creating client...", fg="blue")
            dialog.update()
            
            threading.Thread(target=self._add_client_thread, args=(client_name, dialog, status_label), daemon=True).start()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Create", command=do_add, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)
    
    def _add_client_thread(self, client_name, dialog, status_label):
        """Add client in background"""
        try:
            status_label.config(text="Creating client (this may take 30 seconds)...", fg="blue")
            dialog.update()
            
            response = self.session.post(
                f"{API_BASE}/clients",
                json={"name": client_name},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    message = data.get('message', 'Client created successfully')
                    self.root.after(0, lambda: status_label.config(text=f"✅ {message} Refreshing...", fg="green"))
                    # Wait longer for server to finish creating client, generating configs, and linking
                    import time
                    time.sleep(5)  # Give it more time - config generation can take a while
                    # Force refresh configs list multiple times
                    self.root.after(0, self.refresh_configs)
                    self.root.after(0, lambda: self.root.after(2000, self.refresh_configs))
                    self.root.after(0, lambda: self.root.after(4000, self.refresh_configs))
                    self.root.after(0, lambda: dialog.after(3000, dialog.destroy))
                else:
                    error = data.get('error', 'Failed to create client')
                    self.root.after(0, lambda: status_label.config(text=f"❌ Error: {error}", fg="red"))
            elif response.status_code == 400:
                # Client might already exist - try to link it
                try:
                    data = response.json()
                    error = data.get('error', '')
                    if 'already exists' in error.lower():
                        self.root.after(0, lambda: status_label.config(
                            text=f"⚠️ Client exists but may not be linked. Try refreshing.", fg="orange"))
                        # Try to refresh anyway
                        import time
                        time.sleep(1)
                        self.root.after(0, self.refresh_configs)
                    else:
                        self.root.after(0, lambda: status_label.config(text=f"❌ Error: {error}", fg="red"))
                except:
                    self.root.after(0, lambda: status_label.config(text=f"❌ Error {response.status_code}", fg="red"))
            elif response.status_code == 401:
                self.root.after(0, lambda: status_label.config(text="Session expired. Please log in again.", fg="red"))
                self.root.after(0, lambda: dialog.after(2000, dialog.destroy))
                self.root.after(0, self.logout)
            elif response.status_code == 403:
                self.root.after(0, lambda: status_label.config(text="Permission denied. You don't have permission to add clients.", fg="red"))
            else:
                error = f"Error {response.status_code}"
                try:
                    data = response.json()
                    error = data.get('error', error)
                except:
                    if response.text:
                        error = response.text[:100]
                self.root.after(0, lambda: status_label.config(text=f"❌ Error: {error}", fg="red"))
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: status_label.config(
                text="⏱️ Request timed out. Client may still be creating. Try refreshing.", fg="orange"))
        except Exception as e:
            self.root.after(0, lambda: status_label.config(text=f"❌ Error: {str(e)}", fg="red"))
    
    def show_debug_info(self):
        """Show debug information"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Debug Information")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)
        
        info = f"""Debug Information
{'='*50}
Username: {self.username}
Role: {self.role}
Logged in: {self.logged_in}
VPS URL: {VPS_URL}
API Base: {API_BASE}

Testing API endpoints...
"""
        text_widget.insert(tk.END, info)
        dialog.update()
        
        def test_apis():
            try:
                # Test /api/my-clients
                response = self.session.get(f"{API_BASE}/my-clients", timeout=10)
                text_widget.insert(tk.END, f"\n/api/my-clients: {response.status_code}\n")
                if response.status_code == 200:
                    data = response.json()
                    text_widget.insert(tk.END, f"Response: {data}\n")
                else:
                    text_widget.insert(tk.END, f"Error: {response.text[:200]}\n")
                
                # Test /api/app/configs
                response = self.session.get(f"{API_BASE}/app/configs", timeout=10)
                text_widget.insert(tk.END, f"\n/api/app/configs: {response.status_code}\n")
                if response.status_code == 200:
                    data = response.json()
                    text_widget.insert(tk.END, f"Response: {data}\n")
                else:
                    text_widget.insert(tk.END, f"Error: {response.text[:200]}\n")
            except Exception as e:
                text_widget.insert(tk.END, f"\nException: {str(e)}\n")
            dialog.update()
        
        ttk.Button(dialog, text="Test APIs", command=test_apis).pack(pady=5)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)
    
    def logout(self):
        """Logout and return to login"""
        self.session = requests.Session()
        self.session.verify = False
        self.username = None
        self.role = None
        self.logged_in = False
        # Stop any running animations
        if hasattr(self, 'login_animation_running'):
            self.login_animation_running = False
        if hasattr(self, 'signup_animation_running'):
            self.signup_animation_running = False
        self.show_login()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = PhazeVPNClient()
    app.run()

if __name__ == '__main__':
    main()
