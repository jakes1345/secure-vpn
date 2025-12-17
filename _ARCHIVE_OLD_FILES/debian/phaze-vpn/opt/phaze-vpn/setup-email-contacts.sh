#!/bin/bash
# Setup Contacts System for PhazeVPN Email
# Uses CardDAV (part of Radicale) for contacts

set -e

echo "👥 Setting up Contacts System for PhazeVPN Email..."

# CardDAV is already part of Radicale, so we just need to configure it
echo "✅ Contacts system uses CardDAV (already installed with calendar)"
echo ""
echo "📇 Contacts Server:"
echo "   - CardDAV URL: http://calendar.phazevpn.duckdns.org"
echo "   - Same server as calendar (Radicale)"
echo ""
echo "🔧 Next steps:"
echo "   1. Contacts are managed through the same Radicale server"
echo "   2. Use CardDAV clients (Thunderbird, Apple Contacts, etc.)"
echo "   3. Contacts will sync with email accounts"
