#!/bin/bash
# Quick push script - run this after creating the repo on GitHub

USERNAME="jakes1345"
REPO_NAME="secure-vpn"

echo "🚀 Pushing to GitHub..."
echo "Repository: $USERNAME/$REPO_NAME"
echo ""

# Remove existing remote if any
git remote remove origin 2>/dev/null

# Add SSH remote
git remote add origin "git@github.com:$USERNAME/$REPO_NAME.git"

# Push
echo "⬆️  Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅✅✅ Successfully pushed to GitHub! ✅✅✅"
    echo ""
    echo "Repository: https://github.com/$USERNAME/$REPO_NAME"
else
    echo ""
    echo "❌ Push failed. Make sure:"
    echo "  1. Repository exists on GitHub"
    echo "  2. Your SSH key is added: https://github.com/settings/keys"
    echo "  3. Test SSH: ssh -T git@github.com"
fi

