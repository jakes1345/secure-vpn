#!/bin/bash
PROGDIR=$(dirname "$(readlink -f "$0")")/phazebrowser-gecko/phazebrowser

# 1. VPN INTEGRATION CHECK
# Check if tun0 (OpenVPN) or wg0 (WireGuard) exists
if ! ip link show | grep -qE "tun|wg"; then
    echo "⚠️ VPN NOT DETECTED - DEV MODE ENABLED (Launching anyway for UI/UX review)"
    # PROD: Uncomment exit 1 to enforce security
    # exit 1
fi

# 2. LAUNCH ENVIRONMENT
export LD_LIBRARY_PATH="$PROGDIR:$LD_LIBRARY_PATH"
export MOZ_APP_NAME="PhazeBrowser"
export MOZ_APP_REMOTINGNAME="PhazeBrowser"
export GTK_THEME=Adwaita:dark 

# 3. EXECUTE PROPER BINARY
echo "⚡ Launching PhazeBrowser Secure Session..."
exec "$PROGDIR/firefox-bin" --name "PhazeBrowser" --class "PhazeBrowser" "$@"
