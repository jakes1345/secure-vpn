# 🔧 WEB PORTAL DIRECTORY CONFUSION - FIX
## Consolidating to Single Location

**Date:** Dec 16, 2025 8:09 PM

---

## 🚨 **PROBLEM IDENTIFIED**

### **Multiple Portal Directories:**
```
/opt/phazevpn/web-portal/          ← Service runs from here (NO app.py!)
/opt/phazevpn-portal/              ← Has app.py (3078 lines)
/opt/secure-vpn/web-portal/        ← Has app.py (old?)
/opt/phaze-vpn/web-portal/         ← Backup/old
```

### **Current Situation:**
```
Systemd Service: WorkingDirectory=/opt/phazevpn/web-portal
Actual app.py: /opt/phazevpn-portal/app.py
Result: BROKEN - service can't find app.py
```

---

## ✅ **SOLUTION**

### **Option 1: Update Service to Use Correct Directory** (Recommended)
```bash
# Change systemd service to point to /opt/phazevpn-portal
sed -i 's|/opt/phazevpn/web-portal|/opt/phazevpn-portal|g' /etc/systemd/system/phazevpn-portal.service
systemctl daemon-reload
systemctl restart phazevpn-portal
```

### **Option 2: Copy Files to Service Directory**
```bash
# Copy all files from /opt/phazevpn-portal to /opt/phazevpn/web-portal
rsync -av /opt/phazevpn-portal/ /opt/phazevpn/web-portal/
systemctl restart phazevpn-portal
```

---

## 🎯 **IMPLEMENTING FIX NOW**

Using Option 2 (safer - doesn't change service config)
