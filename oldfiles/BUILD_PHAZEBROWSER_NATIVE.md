# How to Build PhazeBrowser (Native/Gecko)

This guide documents the process of creating the PhazeBrowser natively using a customized Firefox ESR base.

## Why this approach?
Compiling a browser engine (Chromium/Gecko) from source takes 24GB+ RAM and 12+ hours.
This approach "Resource Hacks" a binary distribution to achieve 95% of the customization in 5 minutes.

## The Recipe

### 1. The Base
We use **Firefox ESR** (Extended Support Release) for stability.
- URL: `https://download.mozilla.org/?product=firefox-esr-latest-ssl&os=linux64&lang=en-US`

### 2. The Policies (`distribution/policies.json`)
We inject an Enterprise Policy file that the engine reads on startup.
This forces:
- **Homepage:** `https://phazevpn.com/dashboard`
- **Extensions:** uBlock Origin (Pre-installed)
- **Telemetry:** DISABLED (No sending data to Mozilla)
- **Search:** DuckDuckGo (Private default)

### 3. The Rebrand
- `application.ini`: Modified to set `Name=PhazeBrowser`
- Launcher Wrapper: Exports `MOZ_APP_NAME="PhazeBrowser"` to trick the window manager.

## How to Re-Build (On VPS)

```bash
# 1. Clean workspace
rm -rf /mnt/extra-disk/phazefox_build/*
cd /mnt/extra-disk/phazefox_build

# 2. Download Base
wget -O firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-esr-latest-ssl&os=linux64&lang=en-US"
tar xjf firefox.tar.bz2
mv firefox phazebrowser

# 3. Apply Policies
mkdir -p phazebrowser/distribution
# (Cat the policies.json file here)

# 4. Apply Rebranding
sed -i "s/Name=Firefox/Name=PhazeBrowser/" phazebrowser/application.ini

# 5. Pack
tar cJf PhazeBrowser-Linux.tar.xz phazebrowser
```

## Updates
To update, simply delete the old folder, download the new Firefox ESR tarball, and re-apply steps 3-5.
