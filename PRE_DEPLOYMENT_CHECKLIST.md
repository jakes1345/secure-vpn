# 🔍 PRE-DEPLOYMENT CHECKLIST

**Run this before executing `deploy_production.sh`**

---

## ✅ Local System Checks

### 1. Required Files Exist
```bash
# Check if all required files are present
ls -lh /media/jack/Liunux/secure-vpn/web-portal/requirements.txt
ls -lh /media/jack/Liunux/secure-vpn/deploy_production.sh
```

**Expected:** Both files should exist

---

### 2. Script is Executable
```bash
chmod +x /media/jack/Liunux/secure-vpn/deploy_production.sh
```

---

## ✅ VPS Connectivity Checks

### 1. SSH Connection
```bash
ssh -o ConnectTimeout=10 root@51.222.13.218 "echo 'VPS Connected'"
```

**Expected:** Should print "VPS Connected"

**If fails:**
- Check if VPS is running
- Verify SSH key is configured
- Check firewall rules (port 22)

---

### 2. Required Directories Exist
```bash
ssh root@51.222.13.218 "ls -la /opt/phazevpn/web-portal/app.py"
```

**Expected:** Should show app.py file

---

### 3. VPN Server Binary Exists (Optional)
```bash
ssh root@51.222.13.218 "ls -la /opt/phazevpn/phazevpn-server"
```

**Expected:** Should show phazevpn-server binary (or warning if not found)

---

## ✅ VPS System Checks

### 1. Check Current Services
```bash
ssh root@51.222.13.218 "ps aux | grep -E '(python3 app.py|phazevpn-server)' | grep -v grep"
```

**Expected:** Should show running processes (will be stopped during deployment)

---

### 2. Check Nginx Status
```bash
ssh root@51.222.13.218 "systemctl status nginx --no-pager"
```

**Expected:** Should be active (running)

---

### 3. Check MySQL Status
```bash
ssh root@51.222.13.218 "systemctl status mysql --no-pager"
```

**Expected:** Should be active (running)

---

### 4. Check Disk Space
```bash
ssh root@51.222.13.218 "df -h /opt"
```

**Expected:** Should have at least 2GB free

---

### 5. Check SSL Certificates (Optional)
```bash
ssh root@51.222.13.218"test -f /etc/letsencrypt/live/phazevpn.com/fullchain.pem && echo 'SSL certificates found' || echo 'SSL certificates NOT found (will use HTTP)'"
```

**Expected:** Either "SSL certificates found" or "SSL certificates NOT found"

---

## ✅ What the Script Will Do

### Automatic Actions:
1. ✅ Remove test files (`test-*.py`)
2. ✅ Remove old backup directories
3. ✅ Install Python dependencies from `requirements.txt`
4. ✅ Create 2-3 systemd services:
   - `phazevpn-web.service` (always)
   - `phazevpn-server.service` (if binary exists)
5. ✅ Configure Nginx reverse proxy
   - HTTPS if SSL certs exist
   - HTTP if SSL certs don't exist
6. ✅ Install and configure fail2ban
7. ✅ Install and start Redis
8. ✅ Stop old nohup processes
9. ✅ Start new systemd services
10. ✅ Configure automated daily backups

### Manual Confirmation Required:
- Script will ask "Continue? (y/N)" before making changes

---

## ✅ Script Safety Features

### Pre-Flight Checks:
- ✅ Verifies VPS connectivity
- ✅ Checks if required files exist locally
- ✅ Checks if required directories exist on VPS
- ✅ Checks if app.py exists
- ✅ Detects if VPN server binary exists
- ✅ Detects if SSL certificates exist

### Error Handling:
- ✅ Exits on any command failure (`set -euo pipefail`)
- ✅ Validates file copies
- ✅ Tests Nginx configuration before reload
- ✅ Gracefully handles missing components

### Fallbacks:
- ✅ HTTP-only Nginx config if SSL not available
- ✅ Skips VPN server service if binary not found
- ✅ Continues if test files don't exist

---

## ✅ Post-Deployment Verification

After running the script, verify:

### 1. Services Running
```bash
ssh root@51.222.13.218 'systemctl status phazevpn-web'
ssh root@51.222.13.218 'systemctl status phazevpn-server'  # if exists
```

### 2. Nginx Working
```bash
curl -I https://phazevpn.com  # or http:// if no SSL
```

### 3. fail2ban Active
```bash
ssh root@51.222.13.218 'fail2ban-client status'
```

### 4. Redis Running
```bash
ssh root@51.222.13.218 'redis-cli ping'
```

### 5. Backups Configured
```bash
ssh root@51.222.13.218 'crontab -l | grep backup'
```

### 6. Check Logs
```bash
ssh root@51.222.13.218 'journalctl -u phazevpn-web -n 50'
```

---

## 🚀 Ready to Deploy?

### Quick Check:
```bash
cd /media/jack/Liunux/secure-vpn

# 1. Verify SSH works
ssh root@51.222.13.218 "echo 'OK'"

# 2. Verify files exist
ls -lh web-portal/requirements.txt deploy_production.sh

# 3. Make executable
chmod +x deploy_production.sh

# 4. Run deployment
./deploy_production.sh
```

---

## ⚠️ Troubleshooting

### If SSH times out:
```bash
# Check VPS status
ping 51.222.13.218

# Try with verbose SSH
ssh -v root@51.222.13.218
```

### If Nginx test fails:
```bash
# Check Nginx syntax
ssh root@51.222.13.218 'nginx -t'

# View Nginx error log
ssh root@51.222.13.218 'tail -50 /var/log/nginx/error.log'
```

### If service won't start:
```bash
# Check service status
ssh root@51.222.13.218 'systemctl status phazevpn-web -l'

# View journal logs
ssh root@51.222.13.218 'journalctl -u phazevpn-web -n 100'
```

### If dependencies fail to install:
```bash
# Check pip version
ssh root@51.222.13.218 'pip3 --version'

# Try manual install
ssh root@51.222.13.218 'cd /opt/phazevpn/web-portal && pip3 install -r requirements.txt -v'
```

---

## 📋 Rollback Plan

If something goes wrong:

### 1. Restore old services
```bash
ssh root@51.222.13.218 'cd /opt/phazevpn/web-portal && nohup python3 app.py > /var/log/phazeweb.log 2>&1 &'
```

### 2. Stop new services
```bash
ssh root@51.222.13.218 'systemctl stop phazevpn-web phazevpn-server'
```

### 3. Restore old Nginx config (if you have backup)
```bash
ssh root@51.222.13.218 'cp /etc/nginx/sites-available/phazevpn.backup /etc/nginx/sites-available/phazevpn && systemctl reload nginx'
```

---

## ✅ All Checks Passed?

**If all checks pass, you're ready to deploy:**

```bash
./deploy_production.sh
```

**The script will:**
- Show what it will do
- Ask for confirmation
- Execute all changes
- Verify services started
- Show next steps

**Total time:** ~5-10 minutes

---

**Good luck! 🚀**
