PhazeVPN Client - Linux Installation
====================================

INSTALLATION:
1. Extract this archive:
   tar -xzf phaze-vpn-client-*.tar.gz
   cd phaze-vpn-client-*/

2. Run the GUI:
   ./phaze-vpn-gui

REQUIREMENTS:
- Python 3.6 or later
- tkinter (usually python3-tk package)
- Internet connection to connect to VPS

DEPENDENCIES:
The launcher will automatically install Python dependencies.
If you prefer manual installation:
  pip3 install --user -r requirements.txt

SYSTEM REQUIREMENTS:
- Linux (any distribution)
- 100MB free disk space
- Network access to phazevpn.com

TROUBLESHOOTING:
If tkinter is missing:
  Ubuntu/Debian: sudo apt-get install python3-tk
  Fedora: sudo dnf install python3-tkinter
  Arch: sudo pacman -S tk

For more help, visit: https://phazevpn.com
