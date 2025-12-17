#!/usr/bin/env bash
PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SCRIPT="${PH_DIR}/30-build-desktop.sh"
NEW_URL="https://codeload.github.com/labwc/labwc/tar.gz/refs/tags/v0.7.0"
sed -i "s|download \".*labwc/archive/refs/tags/v\${LABWC_VER}.tar.gz\"|download \"${NEW_URL}\"|g" "$SCRIPT"
sed -i "s|labwc-\${LABWC_VER}.tar.gz|labwc-0.7.0.tar.gz|g" "$SCRIPT"
