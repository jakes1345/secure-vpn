#!/bin/bash
# Create a clean GitHub repo without large files

echo "🧹 Creating clean repo for Shannon AI..."

cd /media/jack/Liunux/secure-vpn

# Create a new branch without history
git checkout --orphan clean-main

# Add only the files we want
git add .gitignore README.md
git add phazevpn-protocol-go/
git add phazevpn-web-go/
git add web-portal/
git add phazebrowser-gecko/
git add android-app/
git add ios-app/
git add phazeos-scripts/
git add *.sh
git add *.md

# Commit
git commit -m "Clean repo for Shannon AI analysis - code only, no build artifacts"

# Force push to replace main
git branch -D main
git branch -m main
git push --force origin main

echo "✅ Clean repo pushed to GitHub!"
echo "Now make it private and give Shannon access"
