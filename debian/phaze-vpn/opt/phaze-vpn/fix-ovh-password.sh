#!/bin/bash

# Fix OVH VPS Password Expiration Issue
# This script helps you change the expired password

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
OLD_PASS="QwX8MJJH3fSE"
NEW_PASS="PhazeVPN2025!"

echo "=========================================="
echo "🔐 Fixing OVH VPS Password"
echo "=========================================="
echo ""
echo "⚠️  The VPS password has expired and needs to be changed."
echo ""
echo "We'll connect and change it to: $NEW_PASS"
echo ""

# Try to change password using expect
if command -v expect &> /dev/null; then
    expect << EOF
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "passwd"
expect {
    "password:" {
        send "$OLD_PASS\r"
        expect {
            "New password:" {
                send "$NEW_PASS\r"
                expect "Retype new password:"
                send "$NEW_PASS\r"
                expect eof
            }
            "current password:" {
                send "$OLD_PASS\r"
                expect "New password:"
                send "$NEW_PASS\r"
                expect "Retype new password:"
                send "$NEW_PASS\r"
                expect eof
            }
        }
    }
    timeout { exit 1 }
}
EOF
else
    echo "⚠️  expect not installed. Please change password manually:"
    echo ""
    echo "   ssh $VPS_USER@$VPS_IP"
    echo "   passwd"
    echo ""
    echo "   Enter current password: $OLD_PASS"
    echo "   Enter new password: (choose a strong password)"
    echo ""
    exit 1
fi

echo ""
echo "✅ Password changed! New password: $NEW_PASS"
echo ""
echo "📝 Update OVH-VPS-CREDENTIALS.txt with the new password"

