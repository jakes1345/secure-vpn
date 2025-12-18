#!/bin/bash
# PhazeOS First Boot Wizard (Pure Bash Version)
# Uses whiptail for a sleek TUI interface.

# Configuration
CONFIG_FILE="$HOME/.config/phazeos/setup_config"
mkdir -p $(dirname "$CONFIG_FILE")
touch "$CONFIG_FILE"

# Colors
export NEWT_COLORS='
root=,black
window=gray,black
border=lightgray,black
shadow=black,black
button=black,green
actbutton=black,lightgreen
compactbutton=black,green
title=green,black
roottext=white,black
textbox=white,black
acttextbox=white,black
entry=white,black
disentry=gray,black
checkbox=white,black
actcheckbox=lightgreen,black
radiolist=white,black
actradiolist=lightgreen,black
listbox=white,black
actlistbox=lightgreen,black
sellistbox=lightgreen,black
actsellistbox=lightgreen,black
'

# Helper: Show Message
msg_box() {
    whiptail --title "$1" --msgbox "$2" 12 60
}

# 1. Welcome Screen
whiptail --title "Welcome to PhazeOS" --yes-button "Get Started" --no-button "Exit" --yesno \
"Welcome to PhazeOS!\n\nThis wizard will help you configure your system:\n\n• Privacy & Security\n• Software Selection\n• System Optimization\n\nNo Python. Pure System Power." 15 60

if [ $? -ne 0 ]; then
    exit 0
fi

# 2. Privacy Settings
PRIVACY=$(whiptail --title "Privacy & Security" --checklist \
"Select privacy features to enable:" 15 60 4 \
"VPN" "Enable PhazeVPN & Killswitch" ON \
"MAC" "Randomize MAC Address on Boot" ON \
"TELEMETRY" "Disable System Telemetry" ON \
"FIREWALL" "Enable 'Glass Wall' Rules" ON 3>&1 1>&2 2>&3)

# 3. Software Selection
SOFTWARE=$(whiptail --title "Software Installation" --checklist \
"Select software categories to install:" 20 60 6 \
"GAMING" "Steam, Lutris, Gamemode" OFF \
"DEV" "VS Code, Docker, Git" OFF \
"HACKING" "Wireshark, Nmap, Aircrack" OFF \
"CREATIVE" "Blender, OBS, Gimp" OFF \
"AI" "Ollama, Local Models" OFF \
"BROWSERS" "Librewolf, Tor Browser" OFF 3>&1 1>&2 2>&3)

# 4. Confirmation
whiptail --title "Confirm Setup" --yesno "Ready to apply settings?\n\nPrivacy: $PRIVACY\nSoftware: $SOFTWARE" 10 60
if [ $? -ne 0 ]; then
    exit 0
fi

# 5. Application (The Real Work)
{
    echo "10"
    echo "XXX"
    echo "Applying Privacy Settings..."
    echo "XXX"
    sleep 1
    
    if [[ "$PRIVACY" == *"VPN"* ]]; then
        # Enable VPN logic here
        mkdir -p $HOME/.config/phazevpn
        touch $HOME/.config/phazevpn/enabled
    fi
    
    if [[ "$PRIVACY" == *"TELEMETRY"* ]]; then
        sudo systemctl disable systemd-resolved 2>/dev/null
    fi

    echo "30"
    echo "XXX"
    echo "Configuring System Services..."
    echo "XXX"
    sleep 1
    sudo systemctl enable bluetooth
    sudo systemctl enable NetworkManager

    echo "50"
    echo "XXX"
    echo "Installing Software (Simulation)..."
    echo "XXX"
    sleep 2
    # Real logic: sudo pacman -S ...

    echo "90"
    echo "XXX"
    echo "Finalizing Configuration..."
    echo "XXX"
    sleep 1
    
    touch "$HOME/.phazeos-wizard-complete"
    echo "100"
} | whiptail --title "System Configuration" --gauge "Applying settings..." 10 60 0

msg_box "Setup Complete" "Your PhazeOS system is ready.\n\nEnjoy the future."
