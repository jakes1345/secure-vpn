#!/bin/bash
# Robust download server starter with auto-restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/download-server.log"
PID_FILE="$SCRIPT_DIR/logs/download-server.pid"
ERROR_LOG="$SCRIPT_DIR/logs/download-server-errors.log"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Function to start server
start_server() {
    echo "[$(date)] Starting PhazeVPN Download Server..." >> "$LOG_FILE"
    cd "$SCRIPT_DIR"
    python3 client-download-server.py >> "$LOG_FILE" 2>> "$ERROR_LOG" &
    echo $! > "$PID_FILE"
    echo "[$(date)] Server started with PID: $(cat $PID_FILE)" >> "$LOG_FILE"
}

# Function to check if server is running
check_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            # Check if it's actually responding
            if curl -s http://localhost:8081/ > /dev/null 2>&1; then
                return 0
            else
                echo "[$(date)] Server process exists but not responding" >> "$ERROR_LOG"
                kill $PID 2>/dev/null
                rm -f "$PID_FILE"
                return 1
            fi
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Main loop
while true; do
    if ! check_server; then
        echo "[$(date)] Server not running, starting..." >> "$LOG_FILE"
        start_server
        sleep 5  # Wait for server to start
    else
        sleep 30  # Check every 30 seconds
    fi
done

