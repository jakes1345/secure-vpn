#!/bin/bash
# Setup Shannon AI for PhazeVPN Codebase Analysis

echo "🤖 Setting up Shannon AI for local codebase analysis..."

# Create Shannon workspace
mkdir -p ~/shannon-analysis
cd ~/shannon-analysis

# Clone Shannon
echo "📥 Cloning Shannon..."
git clone https://github.com/KeygraphHQ/shannon.git
cd shannon

# Build Docker image
echo "🐳 Building Shannon Docker image..."
docker build -t shannon:latest .

# Create repos directory and copy your codebase
echo "📂 Preparing codebase..."
mkdir -p repos/phazevpn
cd repos/phazevpn

# Copy only source code (not build artifacts)
echo "Copying source code..."
cp -r /media/jack/Liunux/secure-vpn/phazevpn-protocol-go ./
cp -r /media/jack/Liunux/secure-vpn/phazevpn-web-go ./
cp -r /media/jack/Liunux/secure-vpn/web-portal ./
cp -r /media/jack/Liunux/secure-vpn/phazebrowser-gecko ./
cp -r /media/jack/Liunux/secure-vpn/android-app ./
cp -r /media/jack/Liunux/secure-vpn/ios-app ./
cp -r /media/jack/Liunux/secure-vpn/phazeos-scripts ./
cp /media/jack/Liunux/secure-vpn/README.md ./

cd ../..

# Create config for PhazeVPN
echo "⚙️  Creating Shannon config..."
cat > configs/phazevpn-config.yaml << 'EOF'
authentication:
  login_type: form
  login_url: "https://phazevpn.com/login"
  credentials:
    username: "admin@phazevpn.com"
    password: "TrashyPanther343!@"
  login_flow:
    - "Type $username into the email field"
    - "Type $password into the password field"  
    - "Click the 'Login' button"
  success_condition:
    type: url_contains
    value: "/dashboard"

rules:
  focus:
    - description: "Focus on VPN protocol security"
      type: path
      url_path: "/api/vpn"
    - description: "Test authentication endpoints"
      type: path
      url_path: "/api/auth"
    - description: "Check user management"
      type: path
      url_path: "/api/users"
  
  avoid:
    - description: "Don't test logout"
      type: path
      url_path: "/logout"
    - description: "Skip static assets"
      type: path
      url_path: "/static"
EOF

echo ""
echo "✅ Shannon setup complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Set your Claude API key:"
echo "   export ANTHROPIC_API_KEY='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'"
echo ""
echo "2. Run Shannon analysis:"
echo "   cd ~/shannon-analysis/shannon"
echo "   docker run --rm -it \\"
echo "     --network host \\"
echo "     --cap-add=NET_RAW \\"
echo "     --cap-add=NET_ADMIN \\"
echo "     -e ANTHROPIC_API_KEY=\"\$ANTHROPIC_API_KEY\" \\"
echo "     -e CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000 \\"
echo "     -v \"\$(pwd)/repos:/app/repos\" \\"
echo "     -v \"\$(pwd)/configs:/app/configs\" \\"
echo "     shannon:latest \\"
echo "     \"https://phazevpn.com\" \\"
echo "     \"/app/repos/phazevpn\" \\"
echo "     --config /app/configs/phazevpn-config.yaml"
echo ""
echo "3. For local-only code analysis (no web testing):"
echo "   docker run --rm -it \\"
echo "     -e ANTHROPIC_API_KEY=\"\$ANTHROPIC_API_KEY\" \\"
echo "     -e CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000 \\"
echo "     -v \"\$(pwd)/repos:/app/repos\" \\"
echo "     shannon:latest \\"
echo "     \"file:///app/repos/phazevpn\" \\"
echo "     \"/app/repos/phazevpn\""
echo ""
