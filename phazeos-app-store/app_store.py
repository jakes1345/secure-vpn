#!/usr/bin/env python3
"""
PhazeStore - Visual App Store for PhazeOS
Install anything with one click - no terminal needed
"""

import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QGroupBox, QScrollArea,
                             QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

class PackageInstaller(QThread):
    """Thread for installing packages"""
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, package_name):
        super().__init__()
        self.package_name = package_name
    
    def run(self):
        """Install package"""
        try:
            self.status.emit(f"Installing {self.package_name}...")
            
            # Check if package exists
            result = subprocess.run(
                ['pacman', '-Si', self.package_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Try AUR
                self.status.emit(f"Searching AUR for {self.package_name}...")
                # Would need yay or paru here
                self.finished.emit(False, f"Package {self.package_name} not found")
                return
            
            # Install package
            cmd = ['sudo', 'pacman', '-S', '--noconfirm', self.package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.finished.emit(True, f"{self.package_name} installed successfully!")
            else:
                self.finished.emit(False, f"Error: {result.stderr}")
        
        except Exception as e:
            self.finished.emit(False, str(e))


class PhazeStore(QMainWindow):
    """PhazeStore - Visual App Store"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_categories()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("PhazeStore - Install Anything")
        self.setGeometry(100, 100, 1200, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Header
        header = QLabel("🛍️ PhazeStore")
        header.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        subtitle = QLabel("Install anything. Zero terminal.")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type app name...")
        self.search_bar.textChanged.connect(self.search_packages)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_bar)
        layout.addLayout(search_layout)
        
        # Tabs for categories
        self.tabs = QTabWidget()
        
        # Gaming tab
        self.gaming_list = self.create_package_list([
            ("Steam", "steam", "🎮 Gaming platform"),
            ("Lutris", "lutris", "🎮 Game manager"),
            ("Wine", "wine", "🎮 Windows compatibility"),
            ("Proton", "proton", "🎮 Steam compatibility layer"),
        ])
        self.tabs.addTab(self.gaming_list, "🎮 Gaming")
        
        # Development tab
        self.dev_list = self.create_package_list([
            ("VS Code", "code", "💻 Code editor"),
            ("Git", "git", "💻 Version control"),
            ("Docker", "docker", "💻 Containers"),
            ("Neovim", "neovim", "💻 Terminal editor"),
            ("Go", "go", "💻 Programming language"),
            ("Python", "python", "💻 Programming language"),
            ("Rust", "rust", "💻 Programming language"),
        ])
        self.tabs.addTab(self.dev_list, "💻 Development")
        
        # Hacking tab
        self.hacking_list = self.create_package_list([
            ("Nmap", "nmap", "⚔️ Network scanner"),
            ("Wireshark", "wireshark-qt", "⚔️ Packet analyzer"),
            ("Aircrack-ng", "aircrack-ng", "⚔️ WiFi security"),
            ("Hashcat", "hashcat", "⚔️ Password cracker"),
            ("John", "john", "⚔️ Password cracker"),
            ("Hydra", "hydra", "⚔️ Login cracker"),
            ("Radare2", "radare2", "⚔️ Reverse engineering"),
        ])
        self.tabs.addTab(self.hacking_list, "⚔️ Hacking")
        
        # Creative tab
        self.creative_list = self.create_package_list([
            ("Blender", "blender", "🎨 3D modeling"),
            ("GIMP", "gimp", "🎨 Image editor"),
            ("OBS Studio", "obs-studio", "🎨 Streaming"),
            ("Audacity", "audacity", "🎨 Audio editor"),
            ("Kdenlive", "kdenlive", "🎨 Video editor"),
        ])
        self.tabs.addTab(self.creative_list, "🎨 Creative")
        
        # Privacy tab
        self.privacy_list = self.create_package_list([
            ("Tor", "tor", "🔐 Anonymity network"),
            ("VeraCrypt", "veracrypt", "🔐 Encryption"),
            ("Proxychains", "proxychains", "🔐 Proxy chains"),
            ("Tails", "tails", "🔐 Privacy OS tools"),
        ])
        self.tabs.addTab(self.privacy_list, "🔐 Privacy")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
        """)
    
    def create_package_list(self, packages):
        """Create a list widget with packages"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        
        for name, pkg, desc in packages:
            item = QListWidgetItem(f"{name} - {desc}")
            item.setData(Qt.ItemDataRole.UserRole, pkg)
            list_widget.addItem(item)
        
        list_widget.itemDoubleClicked.connect(self.install_package)
        
        # Install button
        install_btn = QPushButton("Install Selected")
        install_btn.clicked.connect(lambda: self.install_package(list_widget.currentItem()))
        
        layout.addWidget(list_widget)
        layout.addWidget(install_btn)
        widget.setLayout(layout)
        
        return widget
    
    def search_packages(self, text):
        """Search for packages"""
        # Would implement actual search here
        pass
    
    def install_package(self, item):
        """Install selected package"""
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a package.")
            return
        
        package_name = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Install Package",
            f"Install {package_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText(f"Installing {package_name}...")
            
            self.install_thread = PackageInstaller(package_name)
            self.install_thread.status.connect(self.status_label.setText)
            self.install_thread.finished.connect(
                lambda success, msg: self.installation_finished(success, msg)
            )
            self.install_thread.start()
    
    def installation_finished(self, success, message):
        """Handle installation completion"""
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("✅ " + message)
        else:
            QMessageBox.critical(self, "Error", message)
            self.status_label.setText("❌ " + message)
    
    def load_categories(self):
        """Load package categories"""
        # Would load from actual package database
        pass


def main():
    """Run PhazeStore"""
    app = QApplication(sys.argv)
    
    store = PhazeStore()
    store.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
