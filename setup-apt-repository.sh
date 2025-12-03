#!/bin/bash
# Setup APT Repository for PhazeVPN
# This creates a Debian repository that users can add to their system

set -e

REPO_DIR="/var/www/phazevpn-repo"
REPO_URL="https://phazevpn.duckdns.org/repo"
GPG_KEY_NAME="phazevpn-repo"

echo "=========================================="
echo "Setting up PhazeVPN APT Repository"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

# Install required packages
echo "[1/6] Installing required packages..."
apt-get update
apt-get install -y reprepro gnupg2 nginx apache2-utils

# Create repository directory
echo "[2/6] Creating repository directory..."
mkdir -p "$REPO_DIR"/{conf,dists,pool}
chmod 755 "$REPO_DIR"

# Generate GPG key if it doesn't exist
echo "[3/6] Setting up GPG signing key..."
if [ ! -f "$REPO_DIR/gpg-key.asc" ]; then
    echo "   Generating GPG key for repository signing..."
    cat > /tmp/phazevpn-gpg-keygen << 'EOF'
%no-protection
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: PhazeVPN Repository
Name-Email: admin@phazevpn.duckdns.org
Expire-Date: 0
EOF
    gpg --batch --generate-key /tmp/phazevpn-gpg-keygen
    rm /tmp/phazevpn-gpg-keygen
    
    # Export public key
    gpg --armor --export admin@phazevpn.duckdns.org > "$REPO_DIR/gpg-key.asc"
    echo "   ✅ GPG key created"
else
    echo "   ✅ GPG key already exists"
fi

# Create reprepro configuration
echo "[4/6] Creating repository configuration..."
cat > "$REPO_DIR/conf/distributions" << EOF
Origin: PhazeVPN
Label: PhazeVPN Repository
Codename: stable
Architectures: amd64 arm64 all
Components: main
Description: PhazeVPN Official Repository
SignWith: admin@phazevpn.duckdns.org
EOF

cat > "$REPO_DIR/conf/options" << EOF
basedir $REPO_DIR
EOF

# Create incoming directory for new packages
mkdir -p "$REPO_DIR/incoming"

# Setup Nginx to serve the repository
echo "[5/6] Configuring Nginx..."
cat > /etc/nginx/sites-available/phazevpn-repo << EOF
server {
    listen 80;
    server_name phazevpn.duckdns.org;
    
    root $REPO_DIR;
    index index.html;
    
    location /repo {
        alias $REPO_DIR;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        
        # Allow package downloads
        location ~ \.(deb|dsc|tar\.gz|tar\.bz2|tar\.xz)$ {
            add_header Content-Disposition "attachment";
        }
    }
    
    location = /repo/gpg-key.asc {
        alias $REPO_DIR/gpg-key.asc;
        add_header Content-Type "application/pgp-keys";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/phazevpn-repo /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "[6/6] Repository setup complete!"
echo ""
echo "=========================================="
echo "✅ Repository Ready!"
echo "=========================================="
echo ""
echo "Repository location: $REPO_DIR"
echo "Repository URL: $REPO_URL"
echo ""
echo "To add packages to the repository:"
echo "  1. Build your .deb package"
echo "  2. Run: ./add-package-to-repo.sh <package.deb>"
echo ""
echo "Public GPG key location: $REPO_DIR/gpg-key.asc"
echo "Users can add this repository with:"
echo "  curl -sSL $REPO_URL/gpg-key.asc | sudo apt-key add -"
echo "  echo 'deb $REPO_URL stable main' | sudo tee /etc/apt/sources.list.d/phazevpn.list"
echo "  sudo apt update"
echo "  sudo apt install phaze-vpn"

