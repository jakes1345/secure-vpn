#!/usr/bin/env python3
"""
PhazeOS Graphical Installer
Beautiful GUI installer - no terminal needed
"""

import sys
import os
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QCheckBox,
                             QProgressBar, QListWidget, QLineEdit, QComboBox,
                             QGroupBox, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

class InstallThread(QThread):
    """Thread for running installation"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, selected_software):
        super().__init__()
        self.selected_software = selected_software
    
    def run(self):
        """Run installation"""
        try:
            # Update package database
            self.status.emit("Updating package database...")
            self.progress.emit(10)
            subprocess.run(['sudo', 'pacman', '-Sy'], check=True, capture_output=True)
            
            # Install base packages
            self.status.emit("Installing base system...")
            self.progress.emit(30)
            
            # Install selected software
            if self.selected_software:
                self.status.emit(f"Installing {len(self.selected_software)} packages...")
                self.progress.emit(50)
                
                packages = ' '.join(self.selected_software)
                cmd = ['sudo', 'pacman', '-S', '--noconfirm'] + self.selected_software
                subprocess.run(cmd, check=True, capture_output=True)
            
            self.progress.emit(100)
            self.status.emit("Installation complete!")
            self.finished.emit(True)
        
        except subprocess.CalledProcessError as e:
            self.status.emit(f"Error: {e}")
            self.finished.emit(False)


class PhazeInstaller(QMainWindow):
    """PhazeOS Graphical Installer"""
    
    def __init__(self):
        super().__init__()
        self.selected_software = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("PhazeOS Installer")
        self.setGeometry(100, 100, 900, 700)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Title
        title = QLabel("Welcome to PhazeOS")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("The Ultimate Privacy-First Operating System")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Software selection
        software_group = QGroupBox("Select Software to Install")
        software_layout = QVBoxLayout()
        
        # Categories
        categories = {
            "🎮 Gaming": ["steam", "lutris", "wine", "gamemode"],
            "💻 Development": ["code", "git", "docker", "neovim"],
            "⚔️ Hacking Tools": ["nmap", "wireshark-qt", "aircrack-ng", "hashcat"],
            "🎨 Creative": ["blender", "gimp", "obs-studio", "audacity"],
            "🔐 Privacy": ["tor", "veracrypt", "proxychains"],
            "🌐 Browsers": ["firefox", "chromium"],
            "📱 Utilities": ["vlc", "file-roller", "gparted"]
        }
        
        self.checkboxes = {}
        
        for category, packages in categories.items():
            cat_label = QLabel(f"<b>{category}</b>")
            cat_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            software_layout.addWidget(cat_label)
            
            for package in packages:
                cb = QCheckBox(package)
                cb.stateChanged.connect(self.update_selection)
                software_layout.addWidget(cb)
                self.checkboxes[package] = cb
            
            software_layout.addSpacing(10)
        
        software_group.setLayout(software_layout)
        
        # Scroll area for software selection
        scroll = QScrollArea()
        scroll.setWidget(software_group)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Install Selected Software")
        self.install_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.install_btn.clicked.connect(self.start_installation)
        button_layout.addWidget(self.install_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QCheckBox {
                color: #ffffff;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
    
    def update_selection(self):
        """Update selected software list"""
        self.selected_software = [
            pkg for pkg, cb in self.checkboxes.items() 
            if cb.isChecked()
        ]
        
        count = len(self.selected_software)
        self.install_btn.setText(f"Install {count} Package(s)")
    
    def start_installation(self):
        """Start installation process"""
        if not self.selected_software:
            QMessageBox.warning(self, "No Selection", "Please select at least one package.")
            return
        
        # Confirm
        reply = QMessageBox.question(
            self, 
            "Confirm Installation",
            f"Install {len(self.selected_software)} package(s)?\n\nThis may take several minutes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable install button
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Show progress
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        # Start installation thread
        self.install_thread = InstallThread(self.selected_software)
        self.install_thread.progress.connect(self.progress.setValue)
        self.install_thread.status.connect(self.status_label.setText)
        self.install_thread.finished.connect(self.installation_finished)
        self.install_thread.start()
    
    def installation_finished(self, success):
        """Handle installation completion"""
        self.install_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self,
                "Installation Complete",
                "All selected software has been installed successfully!"
            )
            self.status_label.setText("✅ Installation complete!")
        else:
            QMessageBox.critical(
                self,
                "Installation Failed",
                "There was an error during installation. Check terminal for details."
            )


def main():
    """Run installer"""
    app = QApplication(sys.argv)
    
    # Check if running as root
    if os.geteuid() != 0:
        QMessageBox.critical(
            None,
            "Permission Error",
            "This installer must be run as root.\n\nPlease run: sudo python3 installer.py"
        )
        sys.exit(1)
    
    installer = PhazeInstaller()
    installer.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
