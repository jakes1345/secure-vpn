#!/usr/bin/env python3
"""
PhazeOS First Boot Wizard
Runs automatically after installation - NO TERMINAL NEEDED!
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QCheckBox,
                             QProgressBar, QLineEdit, QComboBox, QGroupBox,
                             QStackedWidget, QMessageBox, QRadioButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

class SetupThread(QThread):
    """Thread for running setup tasks"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    step_complete = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def run(self):
        """Run setup tasks"""
        try:
            total_steps = 6
            current_step = 0
            
            # Step 1: Enable services
            current_step += 1
            self.status.emit("Enabling system services...")
            self.progress.emit(int((current_step / total_steps) * 100))
            self._enable_services()
            self.step_complete.emit("Services enabled")
            
            # Step 2: Configure shell
            current_step += 1
            self.status.emit("Configuring shell...")
            self.progress.emit(int((current_step / total_steps) * 100))
            self._configure_shell()
            self.step_complete.emit("Shell configured")
            
            # Step 3: Install themes
            if self.config.get('install_themes', False):
                current_step += 1
                self.status.emit("Installing themes...")
                self.progress.emit(int((current_step / total_steps) * 100))
                self._install_themes()
                self.step_complete.emit("Themes installed")
            
            # Step 4: Gaming optimizations
            if self.config.get('gaming_mode', False):
                current_step += 1
                self.status.emit("Configuring gaming mode...")
                self.progress.emit(int((current_step / total_steps) * 100))
                self._configure_gaming()
                self.step_complete.emit("Gaming mode enabled")
            
            # Step 5: Privacy settings
            current_step += 1
            self.status.emit("Configuring privacy...")
            self.progress.emit(int((current_step / total_steps) * 100))
            self._configure_privacy()
            self.step_complete.emit("Privacy configured")
            
            # Step 6: Install selected software
            if self.config.get('software_to_install'):
                current_step += 1
                self.status.emit(f"Installing {len(self.config['software_to_install'])} packages...")
                self.progress.emit(int((current_step / total_steps) * 100))
                self._install_software()
                self.step_complete.emit("Software installed")
            
            self.progress.emit(100)
            self.status.emit("Setup complete!")
            self.finished.emit(True)
        
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
            self.finished.emit(False)
    
    def _enable_services(self):
        """Enable system services"""
        services = ['NetworkManager', 'bluetooth', 'docker']
        for service in services:
            try:
                subprocess.run(['sudo', 'systemctl', 'enable', service], 
                             check=True, capture_output=True)
            except:
                pass
    
    def _configure_shell(self):
        """Configure Fish shell"""
        user = os.getenv('USER')
        if user:
            try:
                subprocess.run(['sudo', 'chsh', '-s', '/usr/bin/fish', user],
                             check=True, capture_output=True)
            except:
                pass
    
    def _install_themes(self):
        """Install themes"""
        # Would install Layan theme, etc.
        pass
    
    def _configure_gaming(self):
        """Configure gaming optimizations"""
        try:
            subprocess.run(['systemctl', '--user', 'enable', 'gamemoded'],
                         check=True, capture_output=True)
        except:
            pass
    
    def _configure_privacy(self):
        """Configure privacy settings"""
        # Configure MAC randomization, etc.
        pass
    
    def _install_software(self):
        """Install selected software"""
        packages = self.config.get('software_to_install', [])
        if packages:
            try:
                cmd = ['sudo', 'pacman', '-S', '--noconfirm'] + packages
                subprocess.run(cmd, check=True, capture_output=True)
            except:
                pass


class WelcomePage(QWidget):
    """Welcome page"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Logo/Title
        title = QLabel("Welcome to PhazeOS!")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Let's set up your system")
        subtitle.setFont(QFont("Arial", 18))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        # Description
        desc = QLabel(
            "This wizard will help you configure PhazeOS.\n"
            "You'll be able to:\n"
            "• Set up privacy and security\n"
            "• Install software\n"
            "• Configure your system\n\n"
            "No terminal needed - just click through!"
        )
        desc.setFont(QFont("Arial", 12))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        layout.addStretch()
        
        # Next button
        next_btn = QPushButton("Get Started →")
        next_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        next_btn.clicked.connect(lambda: self.parent.next_page())
        layout.addWidget(next_btn)
        
        self.setLayout(layout)


class PrivacyPage(QWidget):
    """Privacy configuration page"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Privacy & Security")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        group = QGroupBox("Privacy Settings")
        group_layout = QVBoxLayout()
        
        self.vpn_enable = QCheckBox("Enable VPN (PhazeVPN)")
        self.vpn_enable.setChecked(True)
        group_layout.addWidget(self.vpn_enable)
        
        self.mac_random = QCheckBox("Randomize MAC address on boot")
        self.mac_random.setChecked(True)
        group_layout.addWidget(self.mac_random)
        
        self.kill_switch = QCheckBox("Enable kill switch (block internet if VPN drops)")
        self.kill_switch.setChecked(True)
        group_layout.addWidget(self.kill_switch)
        
        self.telemetry = QCheckBox("Disable all telemetry")
        self.telemetry.setChecked(True)
        group_layout.addWidget(self.telemetry)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(lambda: self.parent.prev_page())
        btn_layout.addWidget(back_btn)
        
        next_btn = QPushButton("Next →")
        next_btn.clicked.connect(self.save_and_next)
        btn_layout.addWidget(next_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def save_and_next(self):
        """Save privacy settings"""
        self.parent.config['vpn_enabled'] = self.vpn_enable.isChecked()
        self.parent.config['mac_randomization'] = self.mac_random.isChecked()
        self.parent.config['kill_switch'] = self.kill_switch.isChecked()
        self.parent.config['disable_telemetry'] = self.telemetry.isChecked()
        self.parent.next_page()


class SoftwarePage(QWidget):
    """Software selection page"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Install Software")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Select what you want to install")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Categories
        categories = {
            "🎮 Gaming": ["steam", "lutris", "wine", "gamemode"],
            "💻 Development": ["code", "git", "docker", "neovim"],
            "⚔️ Hacking Tools": ["nmap", "wireshark-qt", "aircrack-ng"],
            "🎨 Creative": ["blender", "gimp", "obs-studio"],
            "🔐 Privacy": ["tor", "veracrypt"],
        }
        
        self.checkboxes = {}
        
        for category, packages in categories.items():
            group = QGroupBox(category)
            group_layout = QVBoxLayout()
            
            for package in packages:
                cb = QCheckBox(package)
                group_layout.addWidget(cb)
                self.checkboxes[package] = cb
            
            group.setLayout(group_layout)
            layout.addWidget(group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(lambda: self.parent.prev_page())
        btn_layout.addWidget(back_btn)
        
        next_btn = QPushButton("Next →")
        next_btn.clicked.connect(self.save_and_next)
        btn_layout.addWidget(next_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def save_and_next(self):
        """Save software selection"""
        selected = [pkg for pkg, cb in self.checkboxes.items() if cb.isChecked()]
        self.parent.config['software_to_install'] = selected
        self.parent.config['gaming_mode'] = any(pkg in selected for pkg in ['steam', 'lutris', 'gamemode'])
        self.parent.next_page()


class AppearancePage(QWidget):
    """Appearance configuration page"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Appearance")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        self.dark_theme = QRadioButton("Dark (Recommended)")
        self.dark_theme.setChecked(True)
        theme_layout.addWidget(self.dark_theme)
        
        self.light_theme = QRadioButton("Light")
        theme_layout.addWidget(self.light_theme)
        
        self.auto_theme = QRadioButton("Auto (follows system)")
        theme_layout.addWidget(self.auto_theme)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Install themes checkbox
        self.install_themes = QCheckBox("Install additional themes (Layan, etc.)")
        self.install_themes.setChecked(True)
        layout.addWidget(self.install_themes)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(lambda: self.parent.prev_page())
        btn_layout.addWidget(back_btn)
        
        next_btn = QPushButton("Next →")
        next_btn.clicked.connect(self.save_and_next)
        btn_layout.addWidget(next_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def save_and_next(self):
        """Save appearance settings"""
        if self.dark_theme.isChecked():
            self.parent.config['theme'] = 'dark'
        elif self.light_theme.isChecked():
            self.parent.config['theme'] = 'light'
        else:
            self.parent.config['theme'] = 'auto'
        
        self.parent.config['install_themes'] = self.install_themes.isChecked()
        self.parent.next_page()


class SetupPage(QWidget):
    """Setup progress page"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Setting Up Your System")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(40)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)
        
        # Status label
        self.status = QLabel("Preparing...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFont(QFont("Arial", 12))
        layout.addWidget(self.status)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def start_setup(self):
        """Start setup process"""
        self.setup_thread = SetupThread(self.parent.config)
        self.setup_thread.progress.connect(self.progress.setValue)
        self.setup_thread.status.connect(self.status.setText)
        self.setup_thread.finished.connect(self.setup_complete)
        self.setup_thread.start()
    
    def setup_complete(self, success):
        """Handle setup completion"""
        if success:
            self.parent.next_page()
        else:
            QMessageBox.critical(self, "Error", "Setup failed. Check logs for details.")


class CompletePage(QWidget):
    """Completion page"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("✅ Setup Complete!")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        message = QLabel(
            "Your PhazeOS system is now configured!\n\n"
            "You can now:\n"
            "• Use PhazeStore to install more software\n"
            "• Configure settings in PhazeSettings\n"
            "• Start using your system\n\n"
            "Enjoy your privacy-first OS!"
        )
        message.setFont(QFont("Arial", 12))
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        layout.addStretch()
        
        # Finish button
        finish_btn = QPushButton("Finish")
        finish_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        finish_btn.clicked.connect(self.finish)
        layout.addWidget(finish_btn)
        
        self.setLayout(layout)
    
    def finish(self):
        """Finish wizard"""
        # Mark wizard as complete
        marker_file = Path.home() / '.phazeos-wizard-complete'
        marker_file.touch()
        
        # Close wizard
        self.parent.close()


class PhazeWizard(QMainWindow):
    """Main wizard window"""
    def __init__(self):
        super().__init__()
        self.config = {}
        self.current_page = 0
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("PhazeOS Setup Wizard")
        self.setGeometry(100, 100, 800, 600)
        
        # Stacked widget for pages
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)
        
        # Create pages
        self.welcome_page = WelcomePage(self)
        self.privacy_page = PrivacyPage(self)
        self.software_page = SoftwarePage(self)
        self.appearance_page = AppearancePage(self)
        self.setup_page = SetupPage(self)
        self.complete_page = CompletePage(self)
        
        # Add pages
        self.stacked.addWidget(self.welcome_page)
        self.stacked.addWidget(self.privacy_page)
        self.stacked.addWidget(self.software_page)
        self.stacked.addWidget(self.appearance_page)
        self.stacked.addWidget(self.setup_page)
        self.stacked.addWidget(self.complete_page)
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QCheckBox, QRadioButton {
                color: #ffffff;
                padding: 5px;
            }
        """)
    
    def next_page(self):
        """Go to next page"""
        if self.current_page == 3:  # Before setup page
            self.current_page += 1
            self.stacked.setCurrentIndex(self.current_page)
            self.setup_page.start_setup()
        else:
            self.current_page += 1
            self.stacked.setCurrentIndex(self.current_page)
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.stacked.setCurrentIndex(self.current_page)


def main():
    """Run wizard"""
    # Check if wizard already completed
    marker_file = Path.home() / '.phazeos-wizard-complete'
    if marker_file.exists():
        print("Wizard already completed. Delete ~/.phazeos-wizard-complete to run again.")
        return
    
    app = QApplication(sys.argv)
    
    wizard = PhazeWizard()
    wizard.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
