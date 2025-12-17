#!/bin/bash
#
# PhazeVPN Production Deployment Script - BULLETPROOF VERSION
# This script transforms the development environment into a production-ready deployment
#
# Priority 1 - Critical Issues:
# 1. Remove ALL placeholders (✅ Already fixed in code)
# 2. Add missing dependencies
# 3. Production deployment (systemd, Nginx, SSL)
# 4. Security hardening (fail2ban, headers, HSTS)
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_USER="root"
VPS_HOST="phazevpn.com"
VPS_IP="15.204.11.19"  # Correct OVH VPS IP
LOCAL_DIR="/media/jack/Liunux/secure-vpn"
REMOTE_DIR="/opt/phazevpn"
WEB_PORTAL_DIR="$REMOTE_DIR/web-portal"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=30"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   PhazeVPN Production Deployment Script                   ║${NC}"
echo -e "${BLUE}║   Transforming to Professional-Grade Production           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to run command on VPS with error handling
run_vps() {
    local cmd="$*"
    echo -e "${BLUE}[VPS]${NC} Running: ${cmd:0:80}..."
    if ! ssh $SSH_OPTS "$VPS_USER@$VPS_IP" "$cmd"; then
        echo -e "${RED}✗ Command failed: $cmd${NC}"
        return 1
    fi
    return 0
}

# Function to copy file to VPS with verification
copy_to_vps() {
    local src="$1"
    local dst="$2"
    
    if [[ ! -f "$src" ]]; then
        echo -e "${RED}✗ Source file not found: $src${NC}"
        return 1
    fi
    
    echo -e "${BLUE}[COPY]${NC} $src → $dst"
    if ! scp $SSH_OPTS "$src" "$VPS_USER@$VPS_IP:$dst"; then
        echo -e "${RED}✗ Failed to copy file${NC}"
        return 1
    fi
    return 0
}

# Pre-flight checks
echo -e "${YELLOW}[PRE-FLIGHT] Running checks...${NC}"

# Check if we can connect to VPS
echo -n "  Checking VPS connectivity... "
if ! ssh $SSH_OPTS "$VPS_USER@$VPS_IP" "echo 'OK'" &>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo -e "${RED}Cannot connect to VPS at $VPS_IP${NC}"
    echo -e "${YELLOW}Please check:${NC}"
    echo "  1. VPS is running"
    echo "  2. SSH key is configured"
    echo "  3. Firewall allows SSH (port 22)"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check if required local files exist
echo -n "  Checking local files... "
if [[ ! -f "$LOCAL_DIR/web-portal/requirements.txt" ]]; then
    echo -e "${RED}FAILED${NC}"
    echo -e "${RED}requirements.txt not found at $LOCAL_DIR/web-portal/requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check if remote directories exist
echo -n "  Checking remote directories... "
if ! run_vps "test -d $REMOTE_DIR && test -d $WEB_PORTAL_DIR" &>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo -e "${RED}Remote directories not found. Expected:${NC}"
    echo "  - $REMOTE_DIR"
    echo "  - $WEB_PORTAL_DIR"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check if app.py exists
echo -n "  Checking app.py... "
if ! run_vps "test -f $WEB_PORTAL_DIR/app.py" &>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo -e "${RED}app.py not found at $WEB_PORTAL_DIR/app.py${NC}"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check if VPN server binary exists
echo -n "  Checking VPN server... "
if ! run_vps "test -f $REMOTE_DIR/phazevpn-server" &>/dev/null; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}phazevpn-server not found at $REMOTE_DIR/phazevpn-server${NC}"
    echo -e "${YELLOW}VPN server service will not be started${NC}"
    VPN_SERVER_EXISTS=false
else
    echo -e "${GREEN}OK${NC}"
    VPN_SERVER_EXISTS=true
fi

echo -e "${GREEN}✅ Pre-flight checks passed${NC}"
echo ""

# Ask for confirmation
echo -e "${YELLOW}This script will:${NC}"
echo "  1. Remove test files and old backups"
echo "  2. Install missing Python dependencies"
echo "  3. Create systemd services"
echo "  4. Configure Nginx reverse proxy"
echo "  5. Set up fail2ban"
echo "  6. Install Redis"
echo "  7. Configure automated backups"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi
echo ""

# ============================================
# STEP 1: Cleanup
# ============================================
echo -e "${YELLOW}[1/8] Cleaning up test files and backups...${NC}"
run_vps "cd $WEB_PORTAL_DIR && rm -f test-*.py 2>/dev/null || true"
run_vps "cd $WEB_PORTAL_DIR && rm -rf templates/backup-* 2>/dev/null || true"
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# ============================================
# STEP 2: Dependencies
# ============================================
echo -e "${YELLOW}[2/8] Installing missing Python dependencies...${NC}"
copy_to_vps "$LOCAL_DIR/web-portal/requirements.txt" "$WEB_PORTAL_DIR/requirements.txt"
run_vps "cd $WEB_PORTAL_DIR && pip3 install -r requirements.txt --upgrade --quiet"
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ============================================
# STEP 3: Systemd Services
# ============================================
echo -e "${YELLOW}[3/8] Setting up systemd services...${NC}"

# VPN Server Service (only if binary exists)
if [[ "$VPN_SERVER_EXISTS" == "true" ]]; then
    run_vps "cat > /etc/systemd/system/phazevpn-server.service << 'EOFSERVICE'
[Unit]
Description=PhazeVPN Protocol Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn/phazevpn-protocol-go
ExecStart=/opt/phazevpn/phazevpn-server
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/phazevpn

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOFSERVICE"
    echo "  ✓ Created phazevpn-server.service"
fi

# Web Portal Service
run_vps "cat > /etc/systemd/system/phazevpn-web.service << 'EOFSERVICE'
[Unit]
Description=PhazeVPN Web Portal (Gunicorn)
After=network.target mysql.service
Wants=network-online.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/phazevpn/web-portal
Environment=\"PATH=/usr/bin:/usr/local/bin\"
Environment=\"VPN_SERVER_IP=phazevpn.com\"
Environment=\"VPN_SERVER_PORT=1194\"
Environment=\"HTTPS_ENABLED=true\"
Environment=\"FLASK_ENV=production\"
ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 --worker-class gevent --worker-connections 1000 --access-logfile /var/log/phazevpn-portal-access.log --error-logfile /var/log/phazevpn-portal-error.log app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/phazevpn /var/log

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOFSERVICE"
echo "  ✓ Created phazevpn-web.service"

echo -e "${GREEN}✅ Systemd services created${NC}"
echo ""

# ============================================
# STEP 4: Nginx Configuration
# ============================================
echo -e "${YELLOW}[4/8] Configuring Nginx reverse proxy...${NC}"

# Check if SSL certificates exist
if run_vps "test -f /etc/letsencrypt/live/phazevpn.com/fullchain.pem" &>/dev/null; then
    SSL_ENABLED=true
    echo "  ✓ SSL certificates found"
else
    SSL_ENABLED=false
    echo -e "  ${YELLOW}⚠ SSL certificates not found - will configure HTTP only${NC}"
fi

if [[ "$SSL_ENABLED" == "true" ]]; then
    # Full HTTPS configuration
    run_vps "cat > /etc/nginx/sites-available/phazevpn << 'EOFNGINX'
# PhazeVPN Production Nginx Configuration

# Rate limiting
limit_req_zone \$binary_remote_addr zone=login_limit:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=30r/m;
limit_req_zone \$binary_remote_addr zone=general_limit:10m rate=100r/m;

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.com www.phazevpn.com;
    
    # Allow Let'\''s Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name phazevpn.com www.phazevpn.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/phazevpn.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers '\''ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384'\'';
    ssl_prefer_server_ciphers off;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/phazevpn.com/chain.pem;

    # Security headers
    add_header Strict-Transport-Security \"max-age=63072000; includeSubDomains; preload\" always;
    add_header X-Frame-Options \"SAMEORIGIN\" always;
    add_header X-Content-Type-Options \"nosniff\" always;
    add_header X-XSS-Protection \"1; mode=block\" always;
    add_header Referrer-Policy \"strict-origin-when-cross-origin\" always;
    add_header Content-Security-Policy \"default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\'' https://js.stripe.com; style-src '\''self'\'' '\''unsafe-inline'\'' https://fonts.googleapis.com; font-src '\''self'\'' https://fonts.gstatic.com; img-src '\''self'\'' data: https:; connect-src '\''self'\'' https://api.stripe.com; frame-src https://js.stripe.com;\" always;
    add_header Permissions-Policy \"geolocation=(), microphone=(), camera=()\" always;

    # Logging
    access_log /var/log/nginx/phazevpn-access.log;
    error_log /var/log/nginx/phazevpn-error.log;

    # Max upload size
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /opt/phazevpn/web-portal/static/;
        expires 1y;
        add_header Cache-Control \"public, immutable\";
    }

    # Login endpoint - strict rate limiting
    location ~ ^/(login|signup|api/auth) {
        limit_req zone=login_limit burst=3 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    # API endpoints - moderate rate limiting
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    # All other requests - general rate limiting
    location / {
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOFNGINX"
else
    # HTTP-only configuration (for testing or if SSL not set up yet)
    run_vps "cat > /etc/nginx/sites-available/phazevpn << 'EOFNGINX'
# PhazeVPN Nginx Configuration (HTTP only - SSL not configured)

# Rate limiting
limit_req_zone \$binary_remote_addr zone=login_limit:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=30r/m;
limit_req_zone \$binary_remote_addr zone=general_limit:10m rate=100r/m;

server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.com www.phazevpn.com _;

    # Logging
    access_log /var/log/nginx/phazevpn-access.log;
    error_log /var/log/nginx/phazevpn-error.log;

    # Max upload size
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /opt/phazevpn/web-portal/static/;
        expires 1y;
        add_header Cache-Control \"public, immutable\";
    }

    # Login endpoint - strict rate limiting
    location ~ ^/(login|signup|api/auth) {
        limit_req zone=login_limit burst=3 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    # API endpoints - moderate rate limiting
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    # All other requests - general rate limiting
    location / {
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOFNGINX"
fi

# Enable the site and test configuration
run_vps "ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn"
if run_vps "nginx -t" &>/dev/null; then
    run_vps "systemctl reload nginx"
    echo -e "${GREEN}✅ Nginx configured and reloaded${NC}"
else
    echo -e "${RED}✗ Nginx configuration test failed${NC}"
    run_vps "nginx -t" || true
    exit 1
fi
echo ""

# ============================================
# STEP 5: fail2ban
# ============================================
echo -e "${YELLOW}[5/8] Installing and configuring fail2ban...${NC}"
run_vps "apt-get update -qq && apt-get install -y fail2ban -qq"

# Create fail2ban jail
run_vps "cat > /etc/fail2ban/jail.d/phazevpn.conf << 'EOFF2B'
[phazevpn-auth]
enabled = true
port = http,https
filter = phazevpn-auth
logpath = /var/log/phazevpn-portal-access.log
maxretry = 5
findtime = 600
bantime = 3600
action = iptables-multiport[name=phazevpn, port=\"http,https\"]

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/phazevpn-error.log
maxretry = 3
findtime = 60
bantime = 600
EOFF2B"

# Create fail2ban filter
run_vps "cat > /etc/fail2ban/filter.d/phazevpn-auth.conf << 'EOFF2B'
[Definition]
failregex = ^<HOST> .* \"POST /login HTTP.*\" (401|403)
            ^<HOST> .* \"POST /api/auth.* HTTP.*\" (401|403)
ignoreregex =
EOFF2B"

run_vps "systemctl enable fail2ban"
run_vps "systemctl restart fail2ban"
echo -e "${GREEN}✅ fail2ban configured${NC}"
echo ""

# ============================================
# STEP 6: Redis
# ============================================
echo -e "${YELLOW}[6/8] Installing Redis for session management...${NC}"
run_vps "apt-get install -y redis-server -qq"
run_vps "systemctl enable redis-server"
run_vps "systemctl start redis-server"
echo -e "${GREEN}✅ Redis installed and started${NC}"
echo ""

# ============================================
# STEP 7: Start Services
# ============================================
echo -e "${YELLOW}[7/8] Stopping old services and starting new systemd services...${NC}"

# Stop old nohup processes gracefully
run_vps "pkill -f 'python3 app.py' || true"
run_vps "pkill -f 'phazevpn-server' || true"
sleep 2

# Reload systemd
run_vps "systemctl daemon-reload"

# Enable and start services
if [[ "$VPN_SERVER_EXISTS" == "true" ]]; then
    run_vps "systemctl enable phazevpn-server"
    run_vps "systemctl restart phazevpn-server"
    echo "  ✓ Started phazevpn-server"
fi

run_vps "systemctl enable phazevpn-web"
run_vps "systemctl restart phazevpn-web"
echo "  ✓ Started phazevpn-web"

echo -e "${GREEN}✅ Services started${NC}"
echo ""

# ============================================
# STEP 8: Automated Backups
# ============================================
echo -e "${YELLOW}[8/8] Setting up automated backups...${NC}"

# Create backup script
run_vps "cat > /opt/phazevpn/backup.sh << 'EOFBACKUP'
#!/bin/bash
# PhazeVPN Automated Backup Script
BACKUP_DIR=\"/opt/phazevpn/backups\"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \"\$BACKUP_DIR\"

# Backup MySQL database
mysqldump -u phazevpn_user -p'SecureVPN2024!' phazevpn_db > \"\$BACKUP_DIR/db_\$DATE.sql\" 2>/dev/null || echo \"MySQL backup failed\"

# Backup configs
tar -czf \"\$BACKUP_DIR/configs_\$DATE.tar.gz\" /opt/phazevpn/web-portal/*.py /opt/phazevpn/web-portal/templates /opt/phazevpn/web-portal/static 2>/dev/null || echo \"Config backup failed\"

# Keep only last 7 days of backups
find \"\$BACKUP_DIR\" -name \"*.sql\" -mtime +7 -delete 2>/dev/null
find \"\$BACKUP_DIR\" -name \"*.tar.gz\" -mtime +7 -delete 2>/dev/null

echo \"Backup completed: \$DATE\"
EOFBACKUP"

run_vps "chmod +x /opt/phazevpn/backup.sh"

# Add to crontab (daily at 2 AM)
run_vps "(crontab -l 2>/dev/null | grep -v 'backup.sh'; echo '0 2 * * * /opt/phazevpn/backup.sh >> /var/log/phazevpn-backup.log 2>&1') | crontab -"

echo -e "${GREEN}✅ Automated backups configured${NC}"
echo ""

# ============================================
# Final Status Check
# ============================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ PRODUCTION DEPLOYMENT COMPLETE!                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Summary of changes:${NC}"
echo -e "  ${GREEN}✅${NC} Removed test files and old backups"
echo -e "  ${GREEN}✅${NC} Installed all missing dependencies"
echo -e "  ${GREEN}✅${NC} Created systemd services"
echo -e "  ${GREEN}✅${NC} Configured Nginx reverse proxy $([ "$SSL_ENABLED" == "true" ] && echo "with SSL" || echo "(HTTP only)")"
echo -e "  ${GREEN}✅${NC} Added security headers and rate limiting"
echo -e "  ${GREEN}✅${NC} Configured fail2ban for intrusion prevention"
echo -e "  ${GREEN}✅${NC} Installed Redis for session management"
echo -e "  ${GREEN}✅${NC} Set up automated daily backups"
echo ""

echo -e "${BLUE}Service Status:${NC}"
if [[ "$VPN_SERVER_EXISTS" == "true" ]]; then
    run_vps "systemctl status phazevpn-server --no-pager -l | head -5" || true
fi
run_vps "systemctl status phazevpn-web --no-pager -l | head -5" || true
echo ""

echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Verify services: ${BLUE}ssh root@$VPS_IP 'systemctl status phazevpn-*'${NC}"
echo -e "  2. Check logs: ${BLUE}ssh root@$VPS_IP 'journalctl -u phazevpn-web -f'${NC}"
echo -e "  3. Test website: ${BLUE}$([ "$SSL_ENABLED" == "true" ] && echo "https" || echo "http")://phazevpn.com${NC}"
echo -e "  4. Monitor fail2ban: ${BLUE}ssh root@$VPS_IP 'fail2ban-client status'${NC}"

if [[ "$SSL_ENABLED" == "false" ]]; then
    echo ""
    echo -e "${YELLOW}⚠ SSL not configured. To enable HTTPS:${NC}"
    echo "  1. Install certbot: apt-get install certbot python3-certbot-nginx"
    echo "  2. Get certificate: certbot --nginx -d phazevpn.com -d www.phazevpn.com"
    echo "  3. Re-run this script to update Nginx config"
fi

echo ""
echo -e "${GREEN}Production deployment successful! 🚀${NC}"
