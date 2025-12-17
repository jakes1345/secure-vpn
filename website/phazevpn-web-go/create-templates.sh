#!/bin/bash
cd /media/jack/Liunux/secure-vpn/phazevpn-web-go/templates

# Base template
cat > base.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhazeVPN - Privacy First</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <div class="container">
            <a href="/" class="logo">🔒 PhazeVPN</a>
            <div class="nav-links">
                <a href="/download">Download</a>
                <a href="/login" class="btn-secondary">Login</a>
                <a href="/signup" class="btn-primary">Sign Up</a>
            </div>
        </div>
    </nav>
    <main>{{template "content" .}}</main>
    <footer>
        <p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
    </footer>
</body>
</html>
EOF

# Home page
cat > home.html << 'EOF'
{{define "content"}}
<div class="hero">
    <h1>Your Privacy, Protected</h1>
    <p class="subtitle">Enterprise-grade VPN with zero logs and maximum security</p>
    <div class="cta">
        <a href="/signup" class="btn-primary btn-large">Get Started Free</a>
        <a href="/download" class="btn-secondary btn-large">Download Now</a>
    </div>
</div>

<div class="features">
    <div class="feature-card">
        <div class="icon">🔒</div>
        <h3>Zero Logs</h3>
        <p>We don't track, store, or share your data. Ever.</p>
    </div>
    <div class="feature-card">
        <div class="icon">⚡</div>
        <h3>Lightning Fast</h3>
        <p>Custom protocol optimized for speed</p>
    </div>
    <div class="feature-card">
        <div class="icon">🌍</div>
        <h3>Global Network</h3>
        <p>Servers worldwide for best performance</p>
    </div>
</div>
{{end}}
EOF

# Login page
cat > login.html << 'EOF'
{{define "content"}}
<div class="auth-container">
    <div class="auth-box">
        <h2>Welcome Back</h2>
        {{if .Error}}<div class="error">{{.Error}}</div>{{end}}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn-primary btn-block">Login</button>
        </form>
        <p class="auth-footer">Don't have an account? <a href="/signup">Sign up</a></p>
    </div>
</div>
{{end}}
EOF

# Signup page
cat > signup.html << 'EOF'
{{define "content"}}
<div class="auth-container">
    <div class="auth-box">
        <h2>Create Account</h2>
        {{if .Error}}<div class="error">{{.Error}}</div>{{end}}
        <form method="POST" action="/signup">
            <input type="text" name="username" placeholder="Username" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn-primary btn-block">Sign Up</button>
        </form>
        <p class="auth-footer">Already have an account? <a href="/login">Login</a></p>
    </div>
</div>
{{end}}
EOF

# Dashboard
cat > dashboard.html << 'EOF'
{{define "content"}}
<div class="dashboard">
    <div class="dashboard-header">
        <h1>Welcome, {{.Username}}</h1>
        <a href="/logout" class="btn-secondary">Logout</a>
    </div>
    
    <div class="dashboard-grid">
        <div class="card">
            <h3>VPN Status</h3>
            <div class="status-indicator offline">Disconnected</div>
            <button class="btn-primary">Connect</button>
        </div>
        
        <div class="card">
            <h3>Your Devices</h3>
            <p>No devices configured yet</p>
            <a href="/download" class="btn-secondary">Download Client</a>
        </div>
        
        <div class="card">
            <h3>Subscription</h3>
            <p class="plan-name">Free Plan</p>
            <a href="/upgrade" class="btn-primary">Upgrade</a>
        </div>
    </div>
</div>
{{end}}
EOF

# Download page
cat > download.html << 'EOF'
{{define "content"}}
<div class="download-page">
    <h1>Download PhazeVPN</h1>
    <div class="download-grid">
        <div class="download-card">
            <h3>🪟 Windows</h3>
            <p>Windows 10/11</p>
            <a href="/downloads/phazevpn-windows.exe" class="btn-primary">Download</a>
        </div>
        <div class="download-card">
            <h3>🍎 macOS</h3>
            <p>macOS 11+</p>
            <a href="/downloads/phazevpn-macos.dmg" class="btn-primary">Download</a>
        </div>
        <div class="download-card">
            <h3>🐧 Linux</h3>
            <p>Ubuntu/Debian</p>
            <a href="/downloads/phazevpn-linux.deb" class="btn-primary">Download</a>
        </div>
        <div class="download-card">
            <h3>�� Android</h3>
            <p>Android 8+</p>
            <a href="/downloads/phazevpn-android.apk" class="btn-primary">Download</a>
        </div>
    </div>
</div>
{{end}}
EOF

# Profile page
cat > profile.html << 'EOF'
{{define "content"}}
<div class="profile-page">
    <h1>Profile Settings</h1>
    <div class="profile-section">
        <h3>Account Information</h3>
        <form method="POST">
            <label>Email</label>
            <input type="email" value="user@example.com" readonly>
            
            <label>Username</label>
            <input type="text" value="username" readonly>
            
            <button type="submit" class="btn-primary">Update Profile</button>
        </form>
    </div>
</div>
{{end}}
EOF

echo "✅ All templates created"
