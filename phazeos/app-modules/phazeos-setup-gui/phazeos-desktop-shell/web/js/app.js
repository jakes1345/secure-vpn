// PhazeOS Desktop Shell - Main Application Logic

let ws = null;
let apps = [];
let files = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 PhazeOS Desktop Shell initializing...');

    // Connect WebSocket
    connectWebSocket();

    // Load initial data
    loadSystemInfo();
    loadVPNStatus();
    loadPrivacyStats();
    loadApps();

    // Update time
    updateTime();
    setInterval(updateTime, 1000);

    // Setup search
    setupSearch();

    // Setup card close buttons
    setupCardClose();

    console.log('✅ Desktop Shell ready!');
});

// WebSocket Connection
function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8080/ws');

    ws.onopen = () => {
        console.log('✅ WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('⚠️ WebSocket disconnected, reconnecting...');
        setTimeout(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(data) {
    if (data.type === 'system_update') {
        // Update system stats in real-time
        console.log('System update:', data.data);
    }
}

// Load System Info
async function loadSystemInfo() {
    try {
        const response = await fetch('/api/system');
        const data = await response.json();
        console.log('System info:', data);
    } catch (error) {
        console.error('Error loading system info:', error);
    }
}

// Load VPN Status
async function loadVPNStatus() {
    try {
        const response = await fetch('/api/vpn');
        const data = await response.json();

        // Update topbar
        document.getElementById('vpn-server').textContent = data.connected ? data.server : 'Disconnected';
        document.getElementById('vpn-status').classList.toggle('connected', data.connected);
        document.getElementById('vpn-status').classList.toggle('disconnected', !data.connected);

        // Update VPN card
        document.getElementById('vpn-status-text').textContent = data.connected ? 'Connected' : 'Disconnected';
        document.getElementById('vpn-server-text').textContent = data.server;
        document.getElementById('vpn-ip').textContent = data.ip;
        document.getElementById('vpn-download').textContent = data.bandwidth.download;
        document.getElementById('vpn-upload').textContent = data.bandwidth.upload;
        document.getElementById('vpn-indicator').classList.toggle('connected', data.connected);
        document.getElementById('vpn-indicator').classList.toggle('disconnected', !data.connected);
    } catch (error) {
        console.error('Error loading VPN status:', error);
    }
}

// Load Privacy Stats
async function loadPrivacyStats() {
    try {
        const response = await fetch('/api/privacy');
        const data = await response.json();

        document.getElementById('trackers-blocked').textContent = data.trackers_blocked;
        document.getElementById('trackers-count').textContent = data.trackers_blocked;
        document.getElementById('ads-count').textContent = data.ads_blocked;
    } catch (error) {
        console.error('Error loading privacy stats:', error);
    }
}

// Load Apps
async function loadApps() {
    try {
        const response = await fetch('/api/apps');
        apps = await response.json();
        console.log('Loaded apps:', apps);
    } catch (error) {
        console.error('Error loading apps:', error);
    }
}

// Update Time
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
    document.getElementById('time').textContent = timeString;
}

// Search Functionality
function setupSearch() {
    const searchInput = document.getElementById('search');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();

        if (query.length === 0) {
            searchResults.classList.add('hidden');
            return;
        }

        // Search apps
        const results = apps.filter(app =>
            app.name.toLowerCase().includes(query) ||
            app.description.toLowerCase().includes(query)
        );

        if (results.length > 0) {
            searchResults.innerHTML = results.map(app => `
                <div class="search-result-item" onclick="launchApp('${app.exec}')">
                    <span class="result-icon">${app.icon}</span>
                    <div class="result-info">
                        <strong>${app.name}</strong>
                        <span>${app.description}</span>
                    </div>
                </div>
            `).join('');
            searchResults.classList.remove('hidden');
        } else {
            searchResults.classList.add('hidden');
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });
}

// Card Close Buttons
function setupCardClose() {
    document.querySelectorAll('.card-close').forEach(button => {
        button.addEventListener('click', (e) => {
            const card = e.target.closest('.card');
            card.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => card.remove(), 300);
        });
    });
}

// Show Launcher
function showLauncher() {
    const modal = document.getElementById('launcher-modal');
    const appGrid = document.getElementById('app-grid');

    appGrid.innerHTML = apps.map(app => `
        <div class="app-item" onclick="launchApp('${app.exec}')">
            <div class="app-icon">${app.icon}</div>
            <div class="app-name">${app.name}</div>
        </div>
    `).join('');

    modal.classList.remove('hidden');
}

function hideLauncher() {
    document.getElementById('launcher-modal').classList.add('hidden');
}

// Launch App
async function launchApp(exec) {
    try {
        const response = await fetch('/api/launch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ app: exec })
        });

        const result = await response.json();
        console.log('Launched:', result);
        hideLauncher();
    } catch (error) {
        console.error('Error launching app:', error);
    }
}

// Show Files
async function showFiles() {
    const modal = document.getElementById('files-modal');
    const fileList = document.getElementById('file-list');

    try {
        const response = await fetch('/api/files?path=/home/admin');
        files = await response.json();

        fileList.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-icon">${file.is_dir ? '📁' : '📄'}</div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${file.is_dir ? 'Folder' : formatBytes(file.size)}</div>
                </div>
            </div>
        `).join('');

        modal.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function hideFiles() {
    document.getElementById('files-modal').classList.add('hidden');
}

// Show Settings
function showSettings() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

function hideSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

// Toggle VPN
async function toggleVPN() {
    console.log('Toggle VPN');
    // TODO: Implement VPN toggle
}

// Utility Functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Refresh data periodically
setInterval(() => {
    loadVPNStatus();
    loadPrivacyStats();
}, 5000);
