# SecureVPN Privacy Protector Browser Extension

Blocks WebRTC leaks, canvas fingerprinting, and other browser tracking methods even when using VPN.

## Features

✅ **WebRTC Leak Protection**
- Blocks RTCPeerConnection
- Prevents real IP address leaks
- Blocks getUserMedia (camera/mic) fingerprinting

✅ **Canvas Fingerprinting Protection**
- Adds noise to canvas rendering
- Prevents unique device identification
- Randomizes canvas output

✅ **WebGL Fingerprinting Protection**
- Masks GPU vendor/renderer info
- Prevents graphics card fingerprinting

✅ **Additional Protections**
- Blocks battery API
- Blocks device motion/orientation
- Randomizes timezone offset
- Protects against various tracking methods

## Installation

### Chrome/Edge (Chromium-based)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `browser-extension` folder
5. Extension is now installed!

### Firefox

1. Open Firefox and go to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select `manifest.json` in the browser-extension folder
5. Extension is now installed!

## Testing

After installing, test your privacy:

1. **WebRTC Leak Test**: https://browserleaks.com/webrtc
   - Should show no real IP addresses

2. **Canvas Fingerprint Test**: https://browserleaks.com/canvas
   - Fingerprint should change each time

3. **DNS Leak Test**: https://www.dnsleaktest.com/
   - Should show VPN DNS, not ISP DNS

## Usage

1. Install the extension
2. Click the extension icon to see status
3. Toggle protection on/off as needed
4. Green = Protected, Red = Disabled

## Privacy Policy

This extension:
- ✅ Runs entirely locally (no data sent anywhere)
- ✅ No tracking or analytics
- ✅ Open source code
- ✅ No permissions beyond what's needed

## Development

To modify or build:

1. Edit files in this directory
2. For Chrome: Load unpacked in `chrome://extensions/`
3. For Firefox: Load temporary in `about:debugging`
4. Make changes and reload extension

## Support

For issues or questions, contact SecureVPN support.

## License

Proprietary - SecureVPN

