# Testing PhazeBrowser

## 📋 Prerequisites

Before testing, you need to install Qt6 development packages:

```bash
sudo apt-get update
sudo apt-get install qt6-base-dev qt6-webengine-dev cmake build-essential
```

## 🔨 Build

### Option 1: Use the build script (recommended)
```bash
cd phazebrowser-native
./build.sh
```

### Option 2: Manual build
```bash
cd phazebrowser-native
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

## 🚀 Run

```bash
cd phazebrowser-native/build
./phazebrowser
```

Or if installed:
```bash
phazebrowser
```

## ✅ Test Checklist

### Core Features
- [ ] Browser opens and loads default page (phazevpn.com)
- [ ] URL bar works (type URL and press Enter)
- [ ] Navigation buttons work (Back, Forward, Reload)
- [ ] Tabs work (create new tab, close tab, switch tabs)

### New Features (Just Added)
- [ ] **PDF Viewer** - Open a PDF file (should open in browser)
- [ ] **Spell Check** - Type in a text field, misspelled words should be underlined
- [ ] **Session Restore** - Open multiple tabs, close browser, reopen (tabs should restore)
- [ ] **Tab Pinning** - Right-click tab → "Pin Tab" (tab should move to start)
- [ ] **Tab Muting** - Right-click tab → "Mute Tab" (tab should show 🔇)
- [ ] **Tab Duplication** - Right-click tab → "Duplicate Tab" (new tab with same URL)
- [ ] **Autocomplete** - Type in URL bar (should show suggestions from history/bookmarks)
- [ ] **Reader Mode** - Press `Ctrl+Shift+R` (page should become clean/readable)

### UI Dialogs
- [ ] **Downloads** - Click Downloads button (should show download dialog)
- [ ] **Settings** - Click Settings button (should show settings dialog)
- [ ] **Privacy Dashboard** - Click Privacy button (should show privacy stats)
- [ ] **Password Manager** - Click Password Manager button (should show passwords)
- [ ] **Bookmarks** - Click Bookmarks button (should show bookmarks dialog)
- [ ] **History** - Click History button (should show history dialog)

### VPN Integration
- [ ] VPN status shows in toolbar
- [ ] VPN Connect/Disconnect button works
- [ ] VPN status updates correctly

### Privacy Features
- [ ] Ad blocking works (visit a site with ads)
- [ ] Tracking protection works
- [ ] Privacy stats update

### Developer Tools
- [ ] Press `Ctrl+Shift+I` (DevTools should open)
- [ ] DevTools tabs work (Console, Network, Elements, etc.)

### Keyboard Shortcuts
- [ ] `Ctrl+T` - New tab
- [ ] `Ctrl+F` - Find in page
- [ ] `Ctrl+P` - Print
- [ ] `Ctrl++` - Zoom in
- [ ] `Ctrl+-` - Zoom out
- [ ] `Ctrl+0` - Reset zoom
- [ ] `Ctrl+Shift+R` - Reader mode
- [ ] `Ctrl+Shift+I` - DevTools

## 🐛 Common Issues

### Qt6 Not Found
**Error**: `Could not find a package configuration file provided by "Qt6"`
**Fix**: Install Qt6 packages:
```bash
sudo apt-get install qt6-base-dev qt6-webengine-dev qt6-webenginewidgets-dev
```

### CMake Not Found
**Error**: `cmake: command not found`
**Fix**: Install CMake:
```bash
sudo apt-get install cmake build-essential
```

### Build Errors
If you get compilation errors:
1. Make sure all Qt6 packages are installed
2. Try cleaning build directory: `rm -rf build && mkdir build`
3. Check CMake output for missing dependencies

## 📊 Expected Performance

- **Startup Time**: < 1 second
- **Memory Usage**: ~50-80MB (idle)
- **Memory Usage**: ~100-150MB (with tabs)
- **CPU Usage**: Low (< 5% idle)

## 🎯 What to Test

1. **Basic Navigation** - Open browser, navigate to different sites
2. **Tabs** - Open multiple tabs, switch between them
3. **Session Restore** - Close browser with tabs open, reopen
4. **New Features** - Test all the features we just added
5. **VPN** - Test VPN connection/disconnection
6. **Privacy** - Visit sites with ads/trackers, check if blocked
7. **Downloads** - Download a file, check download dialog
8. **Settings** - Change settings, verify they persist

---

**Ready to test!** 🚀
