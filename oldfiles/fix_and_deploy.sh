#!/bin/bash
#
# Quick Fix: Upload correct Nginx config and continue deployment
#

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"

echo "🔧 Fixing Nginx configuration..."

# Upload the correct Nginx config
echo "  Uploading nginx_phazevpn.conf..."
scp -o StrictHostKeyChecking=no nginx_phazevpn.conf $VPS_USER@$VPS_IP:/etc/nginx/sites-available/phazevpn

# Test Nginx config
echo "  Testing Nginx configuration..."
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "nginx -t"

# Reload Nginx
echo "  Reloading Nginx..."
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "systemctl reload nginx"

echo "✅ Nginx fixed!"
echo ""

# Continue with remaining deployment steps
echo "🚀 Continuing deployment..."

# Install fail2ban
echo "[5/8] Installing fail2ban..."
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'EOF'
apt-get update -qq && apt-get install -y fail2ban -qq

# Create fail2ban jail
cat > /etc/fail2ban/jail.d/phazevpn.conf << 'EOFF2B'
[phazevpn-auth]
enabled = true
port = http,https
filter = phazevpn-auth
logpath = /var/log/phazevpn-portal-access.log
maxretry = 5
findtime = 600
bantime = 3600
action = iptables-multiport[name=phazevpn, port="http,https"]

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/phazevpn-error.log
maxretry = 3
findtime = 60
bantime = 600
EOFF2B

# Create fail2ban filter
cat > /etc/fail2ban/filter.d/phazevpn-auth.conf << 'EOFF2B'
[Definition]
failregex = ^<HOST> .* "POST /login HTTP.*" (401|403)
            ^<HOST> .* "POST /api/auth.* HTTP.*" (401|403)
ignoreregex =
EOFF2B

systemctl enable fail2ban
systemctl restart fail2ban
echo "✅ fail2ban configured"
EOF

# Install Redis
echo "[6/8] Installing Redis..."
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'EOF'
apt-get install -y redis-server -qq
systemctl enable redis-server
systemctl start redis-server
echo "✅ Redis installed"
EOF

# Start services
echo "[7/8] Starting services..."
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'EOF'
# Stop old processes
pkill -f 'python3 app.py' || true
sleep 2

# Reload systemd
systemctl daemon-reload

# Start web service
systemctl enable phazevpn-web
systemctl restart phazevpn-web

echo "✅ Services started"
EOF

# Setup backups
echo "[8/8] Setting up backups..."
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'EOF'
cat > /opt/phazevpn/backup.sh << 'EOFBACKUP'
#!/bin/bash
BACKUP_DIR="/opt/phazevpn/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup MySQL database
mysqldump -u phazevpn_user -p'SecureVPN2024!' phazevpn_db > "$BACKUP_DIR/db_$DATE.sql" 2>/dev/null || echo "MySQL backup failed"

# Backup configs
tar -czf "$BACKUP_DIR/configs_$DATE.tar.gz" /opt/phazevpn/web-portal/*.py /opt/phazevpn/web-portal/templates /opt/phazevpn/web-portal/static 2>/dev/null || echo "Config backup failed"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null

echo "Backup completed: $DATE"
EOFBACKUP

chmod +x /opt/phazevpn/backup.sh

# Add to crontab
(crontab -l 2>/dev/null | grep -v 'backup.sh'; echo '0 2 * * * /opt/phazevpn/backup.sh >> /var/log/phazevpn-backup.log 2>&1') | crontab -

echo "✅ Backups configured"
EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   ✅ DEPLOYMENT COMPLETE!                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Checking service status..."
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "systemctl status phazevpn-web --no-pager -l | head -10"
echo ""
echo "✅ All done! Visit https://phazevpn.com to test"
