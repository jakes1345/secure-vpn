#!/bin/bash
# Set up GitHub Actions for automatic Windows/macOS builds
# This allows building clients without owning Windows/macOS machines

echo "=========================================="
echo "Setting Up GitHub Actions Builds"
echo "=========================================="
echo ""
echo "This will create GitHub Actions workflows to:"
echo "  • Build Windows .exe automatically"
echo "  • Build macOS .app automatically"
echo "  • Upload to your VPS automatically"
echo "  • All FREE with GitHub Actions!"
echo ""

# Create .github/workflows directory
mkdir -p .github/workflows

# Windows build workflow
cat > .github/workflows/build-windows.yml << 'EOF'
name: Build Windows Client

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller requests
    
    - name: Build Windows executable
      run: |
        pyinstaller --onefile ^
          --windowed ^
          --name "PhazeVPN-Client" ^
          --add-data "assets;assets" ^
          --hidden-import=tkinter ^
          --hidden-import=requests ^
          --hidden-import=urllib3 ^
          --clean ^
          vpn-gui.py
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: phazevpn-windows-client
        path: dist/PhazeVPN-Client.exe
    
    - name: Deploy to VPS
      if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
      uses: easingthemes/ssh-deploy@v4
      env:
        SSH_PRIVATE_KEY: ${{ secrets.VPS_SSH_KEY }}
        REMOTE_HOST: ${{ secrets.VPS_HOST }}
        REMOTE_USER: ${{ secrets.VPS_USER }}
        SOURCE: "dist/PhazeVPN-Client.exe"
        TARGET: "/opt/phaze-vpn/web-portal/static/downloads/"
EOF

# macOS build workflow
cat > .github/workflows/build-macos.yml << 'EOF'
name: Build macOS Client

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build-macos:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python3 -m pip install --upgrade pip
        pip3 install pyinstaller requests
    
    - name: Build macOS app
      run: |
        pyinstaller --onefile \
          --windowed \
          --name "PhazeVPN-Client" \
          --osx-bundle-identifier "com.phazevpn.client" \
          --add-data "assets:assets" \
          --hidden-import=tkinter \
          --hidden-import=requests \
          --hidden-import=urllib3 \
          --clean \
          vpn-gui.py
    
    - name: Create DMG
      run: |
        hdiutil create -volname PhazeVPN \
          -srcfolder dist/PhazeVPN-Client.app \
          -ov -format UDZO \
          dist/PhazeVPN-Client.dmg || echo "DMG creation failed, using .app"
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: phazevpn-macos-client
        path: |
          dist/PhazeVPN-Client.app
          dist/PhazeVPN-Client.dmg
    
    - name: Deploy to VPS
      if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
      uses: easingthemes/ssh-deploy@v4
      env:
        SSH_PRIVATE_KEY: ${{ secrets.VPS_SSH_KEY }}
        REMOTE_HOST: ${{ secrets.VPS_HOST }}
        REMOTE_USER: ${{ secrets.VPS_USER }}
        SOURCE: "dist/"
        TARGET: "/opt/phaze-vpn/web-portal/static/downloads/"
EOF

echo "✅ GitHub Actions workflows created!"
echo ""
echo "Next steps:"
echo "  1. Push this to GitHub:"
echo "     git add .github/workflows/"
echo "     git commit -m 'Add GitHub Actions for Windows/macOS builds'"
echo "     git push"
echo ""
echo "  2. Add GitHub Secrets (Settings > Secrets):"
echo "     - VPS_SSH_KEY: Your SSH private key"
echo "     - VPS_HOST: 15.204.11.19 (or phazevpn.com)"
echo "     - VPS_USER: root"
echo ""
echo "  3. GitHub will automatically build on every push!"
echo "     Or trigger manually: Actions > Build Windows Client > Run workflow"
echo ""

