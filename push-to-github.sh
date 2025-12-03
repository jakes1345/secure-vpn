#!/bin/bash
# Script to push secure-vpn to GitHub
# Usage: ./push-to-github.sh <your-github-repo-url>
# Example: ./push-to-github.sh https://github.com/yourusername/secure-vpn.git

if [ -z "$1" ]; then
    echo "❌ Error: Please provide your GitHub repository URL"
    echo ""
    echo "Usage: ./push-to-github.sh <github-repo-url>"
    echo "Example: ./push-to-github.sh https://github.com/yourusername/secure-vpn.git"
    echo ""
    echo "Or if using SSH:"
    echo "  ./push-to-github.sh git@github.com:yourusername/secure-vpn.git"
    exit 1
fi

REPO_URL="$1"

echo "🚀 Pushing secure-vpn to GitHub..."
echo "📍 Repository: $REPO_URL"
echo ""

# Add remote
echo "📡 Adding remote 'origin'..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

# Push to GitHub
echo "⬆️  Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅✅✅ Successfully pushed to GitHub! ✅✅✅"
    echo ""
    echo "Your repository is now available at:"
    echo "  $REPO_URL"
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "  1. Make sure you've created the repository on GitHub first"
    echo "  2. Check your GitHub credentials (use SSH keys or GitHub CLI)"
    echo "  3. If using HTTPS, you may need a Personal Access Token"
    echo ""
    echo "To use SSH (recommended):"
    echo "  1. Generate SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'"
    echo "  2. Add to GitHub: https://github.com/settings/keys"
    echo "  3. Use SSH URL: git@github.com:username/repo.git"
fi

