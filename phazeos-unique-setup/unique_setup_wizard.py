#!/usr/bin/env python3
"""
PhazeOS Unique Setup Wizard
BREAKS ALL THE RULES - Intent-based, visual, fast
"""

import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QCheckBox,
                             QProgressBar, QGroupBox, QGraphicsView, QGraphicsScene,
                             QGraphicsRectItem, QGraphicsTextItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QColor, QBrush, QPen

class UniqueSetupWizard(QMainWindow):
    """PhazeOS Unique Setup - Intent-Based, Visual, Fast"""
    
    def __init__(self):
        super().__init__()
        self.user_intent = None
        self.selected_software = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize unique UI"""
        self.setWindowTitle("PhazeOS Setup - The Different Way")
        self.setGeometry(100, 100, 1000, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Title - Different approach
        title = QLabel("What's this computer for?")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Choose one - we'll configure everything else")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        # Intent cards (visual, not forms)
        intents_group = QGroupBox("")
        intents_layout = QVBoxLayout()
        
        # Intent buttons (big, visual)
        intents = [
            ("🎮", "Gaming Rig", "Steam, Wine, GameMode, Gaming optimizations"),
            ("💻", "Developer Workstation", "VS Code, Git, Docker, Dev tools"),
            ("⚔️", "Security Researcher", "Metasploit, Wireshark, Hacking tools"),
            ("🎨", "Creative Professional", "Blender, GIMP, OBS, Creative suite"),
            ("🔐", "Privacy Maximalist", "Tor, VPN, Encryption, Privacy tools"),
            ("🎯", "Custom", "I'll choose what I want")
        ]
        
        self.intent_buttons = []
        for emoji, name, desc in intents:
            btn = QPushButton(f"{emoji} {name}\n{desc}")
            btn.setFont(QFont("Arial", 12))
            btn.setMinimumHeight(80)
            btn.clicked.connect(lambda checked, n=name: self.select_intent(n))
            intents_layout.addWidget(btn)
            self.intent_buttons.append(btn)
        
        intents_group.setLayout(intents_layout)
        layout.addWidget(intents_group)
        
        layout.addSpacing(20)
        
        # Privacy toggle (big, obvious)
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QVBoxLayout()
        
        privacy_desc = QLabel("Maximum Privacy Mode")
        privacy_desc.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        privacy_layout.addWidget(privacy_desc)
        
        privacy_sub = QLabel("VPN, Kill Switch, MAC Randomization, No Telemetry")
        privacy_layout.addWidget(privacy_sub)
        
        self.privacy_toggle = QCheckBox("Enable Maximum Privacy (Recommended)")
        self.privacy_toggle.setChecked(True)
        self.privacy_toggle.setFont(QFont("Arial", 12))
        privacy_layout.addWidget(self.privacy_toggle)
        
        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)
        
        layout.addStretch()
        
        # Action button
        self.setup_btn = QPushButton("🚀 Make It Awesome")
        self.setup_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.setup_btn.setMinimumHeight(50)
        self.setup_btn.setEnabled(False)
        self.setup_btn.clicked.connect(self.start_setup)
        layout.addWidget(self.setup_btn)
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QCheckBox {
                color: #ffffff;
                padding: 10px;
                font-size: 14px;
            }
        """)
    
    def select_intent(self, intent_name):
        """User selected an intent"""
        self.user_intent = intent_name
        
        # Highlight selected button
        for btn in self.intent_buttons:
            if intent_name in btn.text():
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #00d4aa;
                        color: white;
                        border: 3px solid #00ffcc;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0078d4;
                        color: white;
                    }
                """)
        
        # Enable setup button
        self.setup_btn.setEnabled(True)
        self.setup_btn.setText(f"🚀 Configure as {intent_name}")
        
        # Map intent to software
        intent_software = {
            "Gaming Rig": ["steam", "lutris", "wine", "gamemode"],
            "Developer Workstation": ["code", "git", "docker", "neovim", "go", "python", "rust"],
            "Security Researcher": ["nmap", "wireshark-qt", "aircrack-ng", "hashcat", "metasploit"],
            "Creative Professional": ["blender", "gimp", "obs-studio", "audacity", "kdenlive"],
            "Privacy Maximalist": ["tor", "veracrypt", "proxychains", "wireguard-tools"],
            "Custom": []
        }
        
        self.selected_software = intent_software.get(intent_name, [])
    
    def start_setup(self):
        """Start setup process"""
        if not self.user_intent:
            return
        
        # Show progress window
        self.progress_window = SetupProgressWindow(
            self.user_intent,
            self.selected_software,
            self.privacy_toggle.isChecked()
        )
        self.progress_window.show()
        self.hide()
        self.progress_window.start_setup()


class SetupProgressWindow(QMainWindow):
    """Progress window - visual, not boring"""
    
    def __init__(self, intent, software, privacy_enabled):
        super().__init__()
        self.intent = intent
        self.software = software
        self.privacy_enabled = privacy_enabled
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("PhazeOS Setup")
        self.setGeometry(150, 150, 800, 500)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Title
        title = QLabel(f"Configuring as {self.intent}...")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(30)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)
        
        # Status
        self.status = QLabel("Starting...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFont(QFont("Arial", 12))
        layout.addWidget(self.status)
        
        # Software list
        if self.software:
            software_label = QLabel(f"Installing {len(self.software)} packages:")
            software_label.setFont(QFont("Arial", 10))
            layout.addWidget(software_label)
            
            software_text = QLabel(", ".join(self.software))
            software_text.setWordWrap(True)
            layout.addWidget(software_text)
        
        layout.addStretch()
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 3px;
            }
        """)
    
    def start_setup(self):
        """Start setup thread"""
        self.setup_thread = SetupThread(self.intent, self.software, self.privacy_enabled)
        self.setup_thread.progress.connect(self.progress.setValue)
        self.setup_thread.status.connect(self.status.setText)
        self.setup_thread.finished.connect(self.setup_complete)
        self.setup_thread.start()
    
    def setup_complete(self, success):
        """Show completion"""
        if success:
            self.status.setText("✅ Setup Complete! Your system is ready.")
            QMessageBox.information(self, "Complete", "PhazeOS is configured and ready!")
        else:
            QMessageBox.critical(self, "Error", "Setup failed. Check logs.")


class SetupThread(QThread):
    """Setup thread"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, intent, software, privacy):
        super().__init__()
        self.intent = intent
        self.software = software
        self.privacy = privacy
    
    def run(self):
        """Run setup"""
        try:
            # Would actually run setup commands here
            # This is just a demo
            import time
            
            steps = [
                ("Enabling services...", 20),
                ("Configuring privacy...", 40),
                ("Installing software...", 70),
                ("Finalizing...", 90),
                ("Complete!", 100)
            ]
            
            for status, progress in steps:
                self.status.emit(status)
                self.progress.emit(progress)
                time.sleep(1)
            
            self.finished.emit(True)
        except Exception as e:
            self.status.emit(f"Error: {e}")
            self.finished.emit(False)


def main():
    """Run unique setup wizard"""
    app = QApplication(sys.argv)
    
    wizard = UniqueSetupWizard()
    wizard.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
