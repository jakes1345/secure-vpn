#!/bin/bash
# Auto-start PhazeOS First Boot Wizard
# This runs automatically on first login

WIZARD_MARKER="$HOME/.phazeos-wizard-complete"
WIZARD_SCRIPT="/usr/local/bin/phazeos-wizard"

# Check if wizard already completed
if [ -f "$WIZARD_MARKER" ]; then
    exit 0
fi

# Check if we're in a graphical session
if [ -z "$DISPLAY" ]; then
    exit 0
fi

# Wait for desktop to be ready
sleep 3

# Run wizard
if [ -f "$WIZARD_SCRIPT" ]; then
    "$WIZARD_SCRIPT" &
elif [ -f "/opt/phazeos/first-boot-wizard/phazeos-setup-wizard" ]; then
    /opt/phazeos/first-boot-wizard/phazeos-setup-wizard &
elif [ -f "/opt/phazeos/first-boot-wizard/first_boot_wizard.sh" ]; then
    /bin/bash /opt/phazeos/first-boot-wizard/first_boot_wizard.sh &
fi
