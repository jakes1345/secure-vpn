# PHAZEVPN ECOSYSTEM - SESSION HANDOFF

## CURRENT OBJECTIVE
Building PhazeOS - an all-in-one operating system with gaming, hacking, AI/ML, and privacy tools. The ISO is currently building locally.

---

## VPS INFRASTRUCTURE

**VPS Connection:**
```
IP: 15.204.11.19
User: root
Password: PhazeVPN_57dd69f3ec20_2025
Domain: phazevpn.com
```

**Services Running:**
- VPN Server (OpenVPN, WireGuard, PhazeVPN protocol)
- Web Portal: https://phazevpn.com
- Webmail: https://mail.phazevpn.com
- Stripe Payments: LIVE (real money processing)

**Recent Security Fix:**
- Removed crypto miners (xmrig) and AnyDesk backdoor
- Blocked hacker IP: 165.154.152.199
- Changed root password from `Jakes1328!@` to `PhazeVPN_57dd69f3ec20_2025`

---

## PHAZEOS BUILD (IN PROGRESS)

**Status:** Building locally (NOT on VPS)
**Location:** `/media/jack/Liunux/secure-vpn/phazeos-build/`
**Log File:** `phazeos_build.log`
**Started:** ~17:47 (current time)
**ETA:** 45-60 minutes

**Check Progress:**
```bash
tail -f /media/jack/Liunux/secure-vpn/phazeos_build.log
```

**Build Script:** `build_phazeos_iso.sh` (completely rewritten with researched packages)

**PhazeOS Specs:**
- Kernel: linux-zen (gaming optimized)
- Filesystem: BTRFS (snapshots)
- Desktop: KDE Plasma
- Size: ~8-10GB ISO

**Included Software:**
- Gaming: Steam, Lutris, Heroic, Bottles, MangoHUD, GameMode
- Hacking: Nmap, Wireshark, Aircrack-ng, Hashcat, John, Hydra
- AI/ML: PyTorch, TensorFlow, Jupyter
- Dev: VSCodium, Docker, Git, Godot, Blender
- Browsers: Librewolf + PhazeBrowser (custom)
- Privacy: Bitwarden, VeraCrypt, MAC spoofing

---

## PAYMENT SYSTEM

**Stripe (LIVE):**
- Config: `/opt/phaze-vpn/web-portal/data/payment_settings.json`
- Keys: pk_live_... and sk_live_... (configured)
- Auto-upgrades users on payment
- ⚠️ WARNING: Webhook signature verification NOT implemented (security risk)

---

## KEY FILES

**Local Machine:**
```
Project: /media/jack/Liunux/secure-vpn/
VPS Password: vps_creds.txt
Build Script: build_phazeos_iso.sh
Build Log: phazeos_build.log
```

**VPS:**
```
Web Portal: /opt/phaze-vpn/web-portal/
VPN Server: /opt/phaze-vpn/server/
Downloads: /opt/phaze-vpn/web-portal/static/downloads/
```

---

## DEPLOYMENT

**Deploy to VPS:**
```bash
cd /media/jack/Liunux/secure-vpn
./deploy_all_to_vps.sh
```
(Uses sshpass with embedded password)

**SSH to VPS:**
```bash
sshpass -p 'PhazeVPN_57dd69f3ec20_2025' ssh root@15.204.11.19
```

---

## CREDENTIALS

```
VPS Root: PhazeVPN_57dd69f3ec20_2025
MySQL Root: Jakes1328!@
Local sudo: Jakes1328!@
```

---

## NEXT STEPS

1. **Monitor ISO Build:**
   ```bash
   tail -f phazeos_build.log
   ```

2. **When Build Completes:**
   - ISO will be in: `phazeos-build/out/`
   - Upload to VPS: `/opt/phaze-vpn/web-portal/static/downloads/`
   - Add download link to website

3. **Create PhazeOS Assets:**
   - Custom wallpapers (cyberpunk theme)
   - Post-install theme script
   - Download page on website

4. **Security TODOs:**
   - Implement Stripe webhook signature verification
   - Set up DKIM/SPF for email

---

## IMPORTANT NOTES

- Build is happening LOCALLY (not on VPS) to avoid impacting live services
- User prefers all-in-one OS (not modular)
- No Tor (user doesn't trust it - gov owns nodes)
- Package list is research-based (Garuda, BlackArch, etc.)
- PhazeBrowser is custom Python/WebKit browser

---

## TROUBLESHOOTING

**If build fails:**
```bash
# Check log
cat phazeos_build.log | grep -i error

# Clean and restart
sudo rm -rf phazeos-build/work phazeos-build/out
./build_phazeos_iso.sh
```

**Check VPS services:**
```bash
sshpass -p 'PhazeVPN_57dd69f3ec20_2025' ssh root@15.204.11.19 "systemctl status nginx"
```

---

## BUILD PROGRESS CHECK

Run this to see current status:
```bash
cd /media/jack/Liunux/secure-vpn
tail -n 30 phazeos_build.log
```

Look for:
- "downloading..." = Still fetching packages
- "installing..." = Installing packages
- "SUCCESS!" = Build complete
- "ERROR" = Build failed

---

END OF HANDOFF
