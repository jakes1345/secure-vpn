// SecureVPN Privacy Protector - Popup Script

document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('toggle');
    
    // Load current status
    chrome.storage.local.get(['enabled'], (result) => {
        const enabled = result.enabled !== false;
        if (enabled) {
            toggle.classList.add('active');
        } else {
            toggle.classList.remove('active');
        }
    });
    
    // Toggle protection
    toggle.addEventListener('click', () => {
        const isActive = toggle.classList.contains('active');
        const newState = !isActive;
        
        toggle.classList.toggle('active', newState);
        
        chrome.runtime.sendMessage({
            action: 'toggle',
            enabled: newState
        }, (response) => {
            if (response && response.success) {
                // Update status indicators
                updateStatusIndicators(newState);
            }
        });
    });
    
    function updateStatusIndicators(enabled) {
        const status = enabled ? 'Active' : 'Disabled';
        const className = enabled ? 'protected' : 'unprotected';
        
        document.getElementById('webrtc-status').textContent = status;
        document.getElementById('webrtc-status').className = `status-value ${className}`;
        document.getElementById('canvas-status').textContent = status;
        document.getElementById('canvas-status').className = `status-value ${className}`;
        document.getElementById('fingerprint-status').textContent = enabled ? 'Blocked' : 'Enabled';
        document.getElementById('fingerprint-status').className = `status-value ${className}`;
    }
    
    // Initial status check
    chrome.storage.local.get(['enabled'], (result) => {
        const enabled = result.enabled !== false;
        updateStatusIndicators(enabled);
    });
});

