# PhazeOS Custom Components - PhazeVPN & PhazeBrowser

## 🎯 Custom Components Included

### 1. **PhazeVPN** ✅ PRIMARY VPN
**Status:** Included via script in ISO build
**Location:** `/opt/phazeos/phazevpn-client/`
**What it is:**
- Custom VPN client built for PhazeOS
- Integrated with PhazeOS web portal
- System-wide VPN with kill switch
- GUI client included

**Installation:**
- Automatically copied during ISO build
- Available at: `/opt/phazeos/phazevpn-client/phazevpn-gui`
- Desktop entry created automatically

**Why it's primary:**
- Built specifically for PhazeOS
- Integrated with PhazeOS infrastructure
- Custom protocol optimized for privacy

---

### 2. **PhazeBrowser** ✅ PRIMARY BROWSER
**Status:** Included via script in ISO build
**Location:** `/opt/phazeos/phazebrowser/`
**What it is:**
- Custom browser built for PhazeOS
- VPN-native (routes ALL traffic through VPN)
- Built-in privacy features
- Integrated with PhazeVPN

**Installation:**
- Automatically copied during ISO build
- Available at: `/opt/phazeos/phazebrowser/phazebrowser.py`
- Desktop entry created automatically
- Symlink: `phazebrowser` command

**Dependencies:**
- python
- python-gobject
- python-requests
- webkit2gtk

**Why it's primary:**
- Built specifically for PhazeOS
- VPN-native (no leaks possible)
- Integrated privacy features

---

### 3. **Other Browsers** (Fallback/Compatibility)
- **Firefox** - Standard browser (fallback)
- **Chromium** - Compatibility (for sites that need Chrome engine)
- **Tor Browser** - Optional (install via: `yay -S tor-browser`)

**Why keep Firefox/Chromium:**
- Some sites work better in standard browsers
- PhazeBrowser is VPN-native (might be slower)
- Users can choose

---

### 4. **Other VPNs** (Fallback)
- **WireGuard** - Fast, modern VPN (fallback)
- **OpenVPN** - Compatibility (fallback)

**Why keep them:**
- PhazeVPN might not work in all scenarios
- Users might want alternatives
- Compatibility

---

## 📦 Package Status

### In packages.x86_64:
- ✅ Firefox (fallback browser)
- ✅ Chromium (compatibility browser)
- ✅ WireGuard tools (fallback VPN)
- ✅ OpenVPN (fallback VPN)
- ✅ PhazeBrowser dependencies (python, webkit2gtk, etc.)

### Installed via Scripts:
- ✅ PhazeVPN Client (via entrypoint.sh)
- ✅ PhazeBrowser (via entrypoint.sh)

---

## 🎯 User Experience

### Default Browser:
- **PhazeBrowser** - VPN-native, privacy-focused
- Firefox/Chromium available as alternatives

### Default VPN:
- **PhazeVPN** - Primary, integrated
- WireGuard/OpenVPN available as alternatives

### Installation:
- PhazeVPN and PhazeBrowser installed automatically
- Desktop entries created
- Ready to use out of the box

---

## ✅ Status

**PhazeVPN:** ✅ Included in ISO build
**PhazeBrowser:** ✅ Included in ISO build
**Dependencies:** ✅ Added to packages.x86_64
**Desktop Entries:** ✅ Created automatically
**Symlinks:** ✅ Created for easy access

**Users get PhazeVPN and PhazeBrowser by default!**
