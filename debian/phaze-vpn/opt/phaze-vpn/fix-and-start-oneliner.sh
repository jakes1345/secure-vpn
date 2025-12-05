#!/bin/bash
pkill -9 -f 'python.*app.py'; pkill -9 -f flask; lsof -ti:5000 | xargs kill -9 2>/dev/null; sleep 2; cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /tmp/web.log 2>&1 & sleep 5; echo "Checking status..."; pgrep -f 'python.*app.py' && echo "✅ Running" || (echo "❌ Failed - check /tmp/web.log"); echo ""; echo "Testing download..."; curl -I https://phazevpn.com/download/client/linux | head -10

