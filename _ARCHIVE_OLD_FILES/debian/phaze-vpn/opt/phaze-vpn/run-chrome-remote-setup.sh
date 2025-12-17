#!/bin/bash
# Quick script to run Chrome Remote Desktop setup command

echo "Running Chrome Remote Desktop setup..."
echo ""

DISPLAY= /opt/google/chrome-remote-desktop/start-host \
    --code="4/0Ab32j92pf9I-GnTb5cweIU1JMa069St3JUeroDPOBy3SzlCoSkdT7kw1Q5JcsFkNif10hw" \
    --redirect-url="https://remotedesktop.google.com/_/oauthredirect" \
    --name=$(hostname) \
    --user-name=jack

echo ""
echo "✅ Setup command executed!"
echo "You should now be able to see your computer in the Chrome Remote Desktop app on your phone."

