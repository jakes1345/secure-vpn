#!/bin/bash
# Diagnose web portal crash - Run on VPS

echo "============================================================"
echo "Diagnosing Web Portal Crash"
echo "============================================================"
echo ""

echo "[1/4] Checking error log..."
if [ -f /tmp/web.log ]; then
    echo "=== Last 50 lines of web.log ==="
    tail -50 /tmp/web.log
else
    echo "⚠️  No log file found"
fi
echo ""

echo "[2/4] Testing Python syntax..."
cd /opt/phaze-vpn/web-portal
if python3 -m py_compile app.py 2>&1; then
    echo "✅ Syntax is valid"
else
    echo "❌ Syntax error found!"
    python3 -m py_compile app.py 2>&1
fi
echo ""

echo "[3/4] Testing imports..."
cd /opt/phaze-vpn/web-portal
python3 -c "
import sys
sys.path.insert(0, '/opt/phaze-vpn/web-portal')
try:
    from flask import Flask
    print('✅ Flask import OK')
except Exception as e:
    print(f'❌ Flask import failed: {e}')

try:
    from pathlib import Path
    print('✅ Pathlib import OK')
except Exception as e:
    print(f'❌ Pathlib import failed: {e}')
" 2>&1
echo ""

echo "[4/4] Trying to start web portal (foreground, first 30 lines)..."
cd /opt/phaze-vpn/web-portal
timeout 5 python3 app.py 2>&1 | head -30 || echo "Process exited or timed out"
echo ""

echo "============================================================"
echo "Diagnosis Complete"
echo "============================================================"

