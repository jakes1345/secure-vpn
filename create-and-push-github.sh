#!/bin/bash
# Create GitHub repo and push - using SSH

echo "🚀 Creating GitHub repository and pushing code..."
echo ""

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME
if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ GitHub username required"
    exit 1
fi

# Get repo name
read -p "Enter repository name (default: secure-vpn): " REPO_NAME
REPO_NAME=${REPO_NAME:-secure-vpn}

echo ""
echo "📋 Repository will be: $GITHUB_USERNAME/$REPO_NAME"
read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Cancelled"
    exit 0
fi

# Try to create repo using GitHub API (if token available)
# Otherwise, user needs to create it manually
echo ""
echo "Option 1: Create repo via GitHub CLI (if installed)"
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI found, creating repository..."
    gh repo create "$REPO_NAME" --public --source=. --remote=origin --push 2>&1
    if [ $? -eq 0 ]; then
        echo "✅✅✅ Repository created and pushed! ✅✅✅"
        exit 0
    fi
fi

echo ""
echo "Option 2: Manual creation + SSH push"
echo "1. Create the repository on GitHub:"
echo "   https://github.com/new"
echo "   Name: $REPO_NAME"
echo "   DON'T initialize with README/gitignore/license"
echo ""
read -p "Press Enter after you've created the repository on GitHub..."

# Add remote and push
REPO_URL="git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"

echo ""
echo "📡 Adding remote..."
git remote remove origin 2>/dev/null
git remote add origin "$REPO_URL"

echo "⬆️  Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅✅✅ Successfully pushed to GitHub! ✅✅✅"
    echo ""
    echo "Repository URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "  1. Make sure your SSH key is added to GitHub:"
    echo "     https://github.com/settings/keys"
    echo "  2. Test SSH connection: ssh -T git@github.com"
    echo "  3. Make sure the repository exists on GitHub"
fi

