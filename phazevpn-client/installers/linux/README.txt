PhazeVPN Client - Linux Installation

QUICK INSTALL:
1. Extract this archive
2. Open terminal in the extracted folder
3. Run: bash install.sh

MANUAL INSTALL:
1. Install dependencies:
   sudo apt-get install python3 python3-pip openvpn
   pip3 install requests

2. Make script executable:
   chmod +x phazevpn-client.py

3. Run:
   python3 phazevpn-client.py

TROUBLESHOOTING:
- If "command not found": Add ~/.local/bin to your PATH
- If OpenVPN errors: Install OpenVPN: sudo apt-get install openvpn
- If Python errors: Install Python 3: sudo apt-get install python3

For help, visit: https://phazevpn.duckdns.org/guide
