#!/bin/bash
# PhazeVPN Protocol - Quick Client Creation Script

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <username> [mode] [password]"
    echo ""
    echo "Modes:"
    echo "  normal      - Standard VPN (fast, good privacy)"
    echo "  semi_ghost  - Enhanced privacy (better stealth)"
    echo "  full_ghost  - Maximum stealth (undetectable)"
    echo ""
    echo "Examples:"
    echo "  $0 john                          # Create user 'john' with auto-generated password"
    echo "  $0 jane semi_ghost               # Create user 'jane' with semi ghost mode"
    echo "  $0 bob full_ghost mypassword123  # Create user 'bob' with custom password"
    exit 1
fi

USERNAME="$1"
MODE="${2:-normal}"
PASSWORD="$3"

echo "=========================================="
echo "👤 Creating PhazeVPN Client"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

python3 manage-clients.py create "$USERNAME" ${PASSWORD:+--password "$PASSWORD"} --mode "$MODE"

echo ""
echo "✅ Client created!"
echo ""
echo "📁 Client files saved to:"
echo "   /opt/secure-vpn/phazevpn-client-configs/${USERNAME}.phazevpn"
echo "   /opt/secure-vpn/phazevpn-client-configs/${USERNAME}.py"
echo ""

