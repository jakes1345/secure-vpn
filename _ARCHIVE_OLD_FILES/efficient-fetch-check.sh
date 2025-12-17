#!/bin/bash
# Most efficient: Check once after estimated time
# Run this in background - it will check once after 45 minutes

echo "=========================================="
echo "⏰ EFFICIENT FETCH CHECK"
echo "=========================================="
echo ""
echo "   Will check fetch status in 45 minutes"
echo "   (middle of 30-60 minute range)"
echo ""
echo "   Running in background..."
echo ""

# Wait 45 minutes (2700 seconds) then check
(sleep 2700 && python3 /opt/phaze-vpn/check-fetch-status.py) &

echo "   ✅ Check scheduled!"
echo "   Process ID: $!"
echo ""
echo "   The check will run automatically in 45 minutes"
echo "   You can continue working - no resources used until then"
echo ""
echo "   To check manually anytime:"
echo "   python3 /opt/phaze-vpn/check-fetch-status.py"
echo ""

