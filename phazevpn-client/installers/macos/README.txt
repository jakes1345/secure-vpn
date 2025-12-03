PhazeVPN Client - macOS Installation

QUICK INSTALL:
1. Extract this archive
2. Open Terminal in the extracted folder
3. Run: bash install.sh

MANUAL INSTALL:
1. Install dependencies:
   brew install python3 openvpn
   pip3 install requests

2. Make script executable:
   chmod +x phazevpn-client.py

3. Run:
   python3 phazevpn-client.py

TROUBLESHOOTING:
- If "command not found": Add ~/.local/bin to your PATH in ~/.zshrc or ~/.bash_profile
- If OpenVPN errors: Install OpenVPN: brew install openvpn
- If Python errors: Install Python 3: brew install python3

For help, visit: https://phazevpn.duckdns.org/guide
