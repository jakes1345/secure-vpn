# PhazeVPN: How to Run Everything

## 1. Deploy the VPS components
You need to deploy the VPN Server, Web Portal, and Email Service to your VPS.
I have created a unified script for this.

**Run this command locally:**
```bash
./deploy_all_to_vps.sh
```
*(Enter your VPS root password when prompted)*

This will:
- Upload the fixed Go VPN server.
- Upload the Web Portal.
- Upload the Email Service.
- Install dependencies (Go, Python, etc.) on the VPS.
- Start all services.

## 2. Run the Desktop Client (Locally)
The client connects your computer to the VPN.
I have already fixed and compiled the binary for you.

**Run this command locally:**
```bash
# Go to client directory
cd phazevpn-client

# Run the Python GUI
python3 phazevpn-client.py
```
- A window will open.
- Select **PhazeVPN** protocol.
- Click **Connect**.

## 3. Run the Phaze Web Browser (Locally)
The browser is a secure client application that runs on your computer.

**Run this command locally:**
```bash
# Install dependencies first
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1

# Run the browser
python3 phazebrowser.py
```

## Summary of URLs
Once deployed, your services will be accessible at:
- **Web Portal**: `http://15.204.11.19:5000` (or `https://phazevpn.com` if DNS is set)
- **Email API**: `http://15.204.11.19:5005`
- **VPN Server**: `15.204.11.19:51821` (UDP)
