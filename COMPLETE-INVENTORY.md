# Complete Codebase Inventory

**Generated:** $(date)
**Purpose:** Comprehensive inventory of all files, components, and dependencies

## 📊 Summary

- **Total Routes:** 91
- **Total Templates:** 64
- **Total Static Files:** 10
- **Python Modules:** 30+
- **VPS Sync Scripts:** Multiple

## 🗂️ Directory Structure

```
secure-vpn/
├── web-portal/              # Main web portal application
│   ├── app.py              # Main Flask application (4768+ lines)
│   ├── templates/          # Jinja2 templates (64 files)
│   │   ├── base.html       # Base template
│   │   ├── admin/          # Admin templates
│   │   ├── moderator/      # Moderator templates
│   │   ├── user/           # User templates
│   │   ├── mobile/         # Mobile templates
│   │   └── ...
│   ├── static/             # Static assets
│   │   ├── css/           # Stylesheets
│   │   │   ├── style.css
│   │   │   ├── animations.css
│   │   │   └── easter-eggs.css
│   │   ├── js/            # JavaScript
│   │   │   ├── main.js
│   │   │   └── easter-eggs.js
│   │   └── images/        # Images
│   │       ├── logo-optimized.png
│   │       ├── logo.png
│   │       ├── favicon.png
│   │       └── og-image.png
│   ├── scripts/           # Utility scripts
│   ├── requirements.txt   # Python dependencies
│   └── ...
├── phazevpn-client/        # VPN client application
├── phazevpn-protocol/      # Custom VPN protocol
├── phazevpn-protocol-go/   # Go implementation
├── browser/                # Custom browser
├── browser-extension/      # Browser extension
├── mobile-app/             # Mobile app
├── web-admin/              # React admin panel
├── unified-web-portal/     # Unified portal
└── scripts/                # Deployment scripts
```

## 🛣️ Routes (91 total)

### Public Routes
- `/` - Home page
- `/login` - Login page
- `/signup` - Signup page
- `/guide` - Setup guide
- `/faq` - FAQ page
- `/pricing` - Pricing page
- `/download` - Download page
- `/contact` - Contact/Support
- `/blog` - Blog
- `/testimonials` - Testimonials
- `/privacy` - Privacy policy
- `/terms` - Terms of service
- `/forgot-password` - Password reset request
- `/reset-password` - Password reset form
- `/verify-email` - Email verification
- `/sitemap.xml` - Sitemap
- `/robots.txt` - Robots file

### User Routes
- `/dashboard` - User dashboard
- `/profile` - User profile
- `/config` - VPN config download
- `/download/<client_name>` - Client config download
- `/qr/<client_name>` - QR code for config
- `/2fa/setup` - 2FA setup
- `/2fa/enable` - Enable 2FA
- `/2fa/disable` - Disable 2FA

### Admin Routes
- `/admin` - Admin dashboard
- `/admin/analytics` - Analytics
- `/admin/clients` - Client management
- `/admin/users` - User management
- `/admin/activity` - Activity logs
- `/admin/payments` - Payment management
- `/admin/payment-settings` - Payment settings

### Moderator Routes
- `/moderator` - Moderator dashboard

### Mobile Routes
- `/mobile/monitor` - Mobile monitoring
- `/mobile/client` - Mobile client details

### API Routes
- `/api/vpn/connect` - Connect VPN
- `/api/vpn/disconnect` - Disconnect VPN
- `/api/vpn/status` - VPN status
- `/api/connections` - Connection history
- `/api/clients` - Client management API
- `/api/my-clients` - User's clients
- `/api/tickets` - Support tickets API
- `/api/payments` - Payment API
- `/api/users` - User management API
- `/api/profile` - Profile API
- `/api/stats/bandwidth` - Bandwidth stats
- `/api/server/metrics` - Server metrics
- `/api/app/login` - Mobile app login
- `/api/app/signup` - Mobile app signup
- `/api/app/configs` - Mobile app configs
- `/api/app/servers` - Mobile app servers
- `/api/v1/client/register` - Client registration
- `/api/v1/client/checkin` - Client checkin
- `/api/export/activity` - Export activity
- `/api/export/connections` - Export connections

### Payment Routes
- `/payment` - Payment page
- `/payment/stripe/checkout` - Stripe checkout
- `/payment/success` - Payment success
- `/payment/stripe/webhook` - Stripe webhook

### Download Routes
- `/download/gui` - GUI download
- `/download/client/<platform>` - Platform-specific downloads
- `/download/setup-instructions` - Setup instructions

### Repository Routes
- `/repo/` - APT repository
- `/repo/gpg-key.asc` - GPG key
- `/repo/<filename>` - Repository files

### Other Routes
- `/logo.png` - Logo
- `/images/logo.png` - Logo image
- `/favicon.ico` - Favicon
- `/api/v1/easter-egg/reward` - Easter egg

## 📄 Templates (64 total)

### Base Templates
- `base.html` - Main base template
- `base-new.html` - Alternative base template
- `error.html` - Error page template

### Public Templates
- `home.html` - Home page
- `home-new.html` - Alternative home page
- `login.html` - Login page
- `signup.html` - Signup page
- `guide.html` - Setup guide
- `faq.html` - FAQ page
- `pricing.html` - Pricing page
- `download.html` - Download page
- `download-instructions.html` - Download instructions
- `contact.html` - Contact page
- `blog.html` - Blog page
- `testimonials.html` - Testimonials
- `privacy-policy.html` - Privacy policy
- `terms.html` - Terms of service
- `forgot-password.html` - Forgot password
- `reset-password.html` - Reset password
- `2fa-setup.html` - 2FA setup
- `qr-code.html` - QR code display
- `sitemap.xml` - XML sitemap

### User Templates
- `user/dashboard.html` - User dashboard
- `profile.html` - User profile
- `tickets.html` - Support tickets

### Admin Templates
- `admin/dashboard.html` - Admin dashboard
- `admin/analytics.html` - Analytics
- `admin/clients.html` - Client management
- `admin/users.html` - User management
- `admin/activity.html` - Activity logs
- `admin/payments.html` - Payment management
- `admin/payment-settings.html` - Payment settings

### Moderator Templates
- `moderator/dashboard.html` - Moderator dashboard

### Mobile Templates
- `mobile/monitor.html` - Mobile monitoring
- `mobile/client-detail.html` - Mobile client details

### Payment Templates
- `payment.html` - Payment page
- `payment-success.html` - Payment success

### Other Templates
- `phazebrowser.html` - Browser page
- `backup-20251125-123649/` - Backup templates

## 🎨 Static Files (10 total)

### CSS Files
- `css/style.css` - Main stylesheet
- `css/animations.css` - Animations
- `css/easter-eggs.css` - Easter egg styles

### JavaScript Files
- `js/main.js` - Main JavaScript
- `js/easter-eggs.js` - Easter egg JavaScript
- `analytics.js` - Analytics script

### Images
- `images/logo-optimized.png` - Optimized logo
- `images/logo.png` - Logo
- `images/favicon.png` - Favicon
- `images/og-image.png` - Open Graph image

## 🐍 Python Modules

### Core Modules
- `app.py` - Main Flask application
- `mysql_db.py` - MySQL database interface
- `file_locking.py` - File locking utilities
- `rate_limiting.py` - Rate limiting
- `secure_auth.py` - Authentication utilities

### Email Modules
- `email_api.py` - Email API interface
- `email_smtp.py` - SMTP email
- `email_mailjet.py` - Mailjet integration
- `email_outlook_oauth2.py` - Outlook OAuth2
- `email_util.py` - Email utilities
- `smtp_config.py` - SMTP configuration
- `outlook_oauth2_config.py` - Outlook OAuth2 config

### Payment Modules
- `payment_integrations.py` - Payment integrations
- `payment_integrations_secure.py` - Secure payment integrations

### Other Modules
- `generate_all_protocols.py` - Protocol generation
- `mysql_migration.py` - Database migration

## 📦 Dependencies

### Python Packages (requirements.txt)
- Flask - Web framework
- Flask-WTF - CSRF protection
- bcrypt - Password hashing
- qrcode - QR code generation
- mysql-connector-python - MySQL connector
- requests - HTTP requests
- python-dotenv - Environment variables
- stripe - Stripe payment integration
- paramiko - SSH client (for VPS sync)

### System Dependencies
- Python 3.8+
- MySQL/MariaDB
- Nginx (for reverse proxy)
- OpenVPN
- WireGuard
- OpenSSL

## 🔄 VPS Sync Scripts

### Main Sync Scripts
- `sync-to-vps.sh` - Basic sync script
- `SYNC-TO-VPS.sh` - Alternative sync script
- `sync-all-to-vps-complete.sh` - **COMPREHENSIVE SYNC** (NEW)

### What Gets Synced
1. **Python Files** - All `.py` files in web-portal/
2. **Templates** - All `.html` templates
3. **Static Files** - All CSS, JS, images
4. **Configuration** - requirements.txt, nginx config, service files
5. **Scripts** - All shell scripts

## ⚙️ Configuration Files

### Required Config Files
- `db_config.json` - MySQL database configuration (NOT in repo - gitignored)
- `.env` - Environment variables (NOT in repo - gitignored)
- `nginx-phazevpn.conf` - Nginx configuration
- `phazevpn-portal.service` - Systemd service file

### Optional Config Files
- `pyrightconfig.json` - Type checker config
- `mailgun_config.py` - Mailgun config
- `mailjet_config.py` - Mailjet config

## 🚀 Deployment Checklist

### Before Deploying to VPS
- [ ] Run `comprehensive-audit.py` to check for issues
- [ ] Ensure all dependencies are in `requirements.txt`
- [ ] Verify all templates exist
- [ ] Check all static files are present
- [ ] Create `db_config.json` on VPS
- [ ] Create `.env` file on VPS
- [ ] Test locally first

### Deploying to VPS
1. Run `sync-all-to-vps-complete.sh` to sync all files
2. SSH into VPS: `ssh root@15.204.11.19`
3. Install dependencies: `cd /opt/secure-vpn/web-portal && pip3 install -r requirements.txt`
4. Restart service: `systemctl restart phazevpn-web`
5. Check logs: `journalctl -u phazevpn-web -f`

## 🔍 Missing Files (From Audit)

### Known Missing (Expected)
- `db_config.json` - Gitignored, must be created on VPS
- `.env` - Gitignored, must be created on VPS

### Potentially Missing
- Check audit report: `AUDIT-REPORT.json`

## 📝 Notes

- **Static File Reference Issue:** Backup template `backup-20251125-123649/signup.html` references `/static/style.css` instead of `css/style.css` - this is fine as it's a backup
- **Local Modules:** Some imports like `twofa`, `vpn_manager` are local modules, not packages
- **VPS Path:** VPS uses `/opt/secure-vpn/web-portal` as the web portal path
- **Service Name:** Web portal service is `phazevpn-web` or `secure-vpn-portal`

## 🔗 Related Files

- `comprehensive-audit.py` - Audit script
- `AUDIT-REPORT.json` - Detailed audit report
- `sync-all-to-vps-complete.sh` - Complete sync script
