#!/bin/bash
set -e

# SEARXNG DEPLOYMENT SCRIPT FOR VPS

echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

echo "Docker check..."

cd /opt
if [ ! -d "searxng-docker" ]; then
    git clone https://github.com/searxng/searxng-docker.git
fi
cd searxng-docker

# Generate random secret key
SECRET=$(openssl rand -base64 32)
sed -i "s|ultrasecretkey|$SECRET|g" .env

# Enable image proxy for privacy
sed -i "s|SEARXNG_IMAGE_PROXY=false|SEARXNG_IMAGE_PROXY=true|g" .env

# Configure settings.yml for JSON format if needed, but default is fine.
# We will use the default port 8080 mapped.

echo "Forcing Docker Compose Binary Install..."
apt-get remove -y docker-compose || true
rm -f /usr/bin/docker-compose
curl -SL https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

echo "Starting SearXNG..."
docker-compose up -d

echo "✅ SearXNG is running on port 8080 (via Docker Proxy)"
echo "You may need to configure Nginx/Reverse Proxy to expose it on port 80/443."
