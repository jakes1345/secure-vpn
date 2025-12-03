# 📱 PhazeVPN Mobile App

## Custom VPN App - Like NordVPN/ExpressVPN

This is your custom VPN mobile app that users can download from app stores.

---

## Features:

✅ **One-tap connect/disconnect**  
✅ **Server selection**  
✅ **Connection status**  
✅ **Kill switch**  
✅ **Auto-connect**  
✅ **Beautiful UI**  
✅ **Subscription management**  

---

## Setup Instructions:

### 1. Install Dependencies:
```bash
cd mobile-app
npm install
```

### 2. Configure API:
Edit `src/config/api.js`:
```javascript
export const API_BASE_URL = 'https://phazevpn.duckdns.org';
```

### 3. Run on Android:
```bash
npm run android
```

### 4. Run on iOS:
```bash
npm run ios
```

---

## App Structure:

```
mobile-app/
├── src/
│   ├── screens/
│   │   ├── LoginScreen.js
│   │   ├── HomeScreen.js
│   │   ├── ServersScreen.js
│   │   └── SettingsScreen.js
│   ├── components/
│   │   ├── ConnectButton.js
│   │   └── StatusIndicator.js
│   ├── services/
│   │   ├── api.js
│   │   └── vpn.js
│   └── App.js
```

---

## Integration:

The app connects to your web portal API:
- Login: `/api/app/login`
- Get configs: `/api/app/configs`
- Get servers: `/api/app/servers`
- Check status: `/api/app/connection-status`

---

**Ready to build!** 🚀

