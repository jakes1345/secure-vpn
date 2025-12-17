// SecureVPN Privacy Protector - Background Service Worker

// Set privacy settings on install
chrome.runtime.onInstalled.addListener(() => {
    console.log('[SecureVPN] Extension installed - enabling privacy features');
    
    // Block WebRTC leaks at browser level
    chrome.privacy.network.webRTCIPHandlingPolicy.set({
        value: 'disable_non_proxied_udp'
    }, () => {
        console.log('[SecureVPN] WebRTC leak protection enabled');
    });
    
    // Store installation date
    chrome.storage.local.set({
        installed: new Date().toISOString(),
        enabled: true
    });
});

// Listen for messages from popup/content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'toggle') {
        chrome.storage.local.set({ enabled: request.enabled }, () => {
            sendResponse({ success: true });
        });
        return true;
    }
    
    if (request.action === 'getStatus') {
        chrome.storage.local.get(['enabled'], (result) => {
            sendResponse({ enabled: result.enabled !== false });
        });
        return true;
    }
});

// Check for VPN connection (basic check)
function checkVPNStatus() {
    // This is a simple check - could be enhanced
    fetch('https://api.ipify.org?format=json')
        .then(res => res.json())
        .then(data => {
            chrome.storage.local.set({ lastIP: data.ip });
        })
        .catch(() => {
            // Ignore errors
        });
}

// Check VPN status periodically
chrome.alarms.create('checkVPN', { periodInMinutes: 5 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'checkVPN') {
        checkVPNStatus();
    }
});

