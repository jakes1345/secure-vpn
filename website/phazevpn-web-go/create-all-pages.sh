#!/bin/bash
cd /media/jack/Liunux/secure-vpn/phazevpn-web-go/templates

# Pricing Page
cat > pricing.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pricing - PhazeVPN</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <div class="container">
            <a href="/" class="logo">🔒 PhazeVPN</a>
            <div class="nav-links">
                <a href="/download">Download</a>
                <a href="/pricing">Pricing</a>
                <a href="/login" class="btn-secondary">Login</a>
                <a href="/signup" class="btn-primary">Sign Up</a>
            </div>
        </div>
    </nav>
    <main>
        <div class="download-page">
            <h1>Simple, Transparent Pricing</h1>
            <div class="download-grid">
                <div class="download-card">
                    <h3>Free</h3>
                    <p class="plan-price">$0/month</p>
                    <ul style="text-align: left; color: rgba(255,255,255,0.7);">
                        <li>✓ 10GB/month bandwidth</li>
                        <li>✓ 3 devices</li>
                        <li>✓ Basic locations</li>
                        <li>✓ Zero logs</li>
                    </ul>
                    <a href="/signup" class="btn-primary">Get Started</a>
                </div>
                <div class="download-card">
                    <h3>Pro</h3>
                    <p class="plan-price">$9.99/month</p>
                    <ul style="text-align: left; color: rgba(255,255,255,0.7);">
                        <li>✓ Unlimited bandwidth</li>
                        <li>✓ 10 devices</li>
                        <li>✓ All locations</li>
                        <li>✓ Priority support</li>
                    </ul>
                    <a href="/signup" class="btn-primary">Upgrade</a>
                </div>
                <div class="download-card">
                    <h3>Enterprise</h3>
                    <p class="plan-price">Custom</p>
                    <ul style="text-align: left; color: rgba(255,255,255,0.7);">
                        <li>✓ Dedicated servers</li>
                        <li>✓ Unlimited devices</li>
                        <li>✓ Custom integration</li>
                        <li>✓ 24/7 support</li>
                    </ul>
                    <a href="/contact" class="btn-primary">Contact Us</a>
                </div>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
    </footer>
</body>
</html>
EOF

# FAQ Page
cat > faq.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FAQ - PhazeVPN</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <div class="container">
            <a href="/" class="logo">🔒 PhazeVPN</a>
            <div class="nav-links">
                <a href="/download">Download</a>
                <a href="/faq">FAQ</a>
                <a href="/login" class="btn-secondary">Login</a>
            </div>
        </div>
    </nav>
    <main>
        <div class="dashboard" style="max-width: 900px;">
            <h1>Frequently Asked Questions</h1>
            <div class="card">
                <h3>What is PhazeVPN?</h3>
                <p>PhazeVPN is a privacy-first VPN service with zero logging, custom encryption, and maximum security.</p>
            </div>
            <div class="card">
                <h3>Do you keep logs?</h3>
                <p>Absolutely not. We don't track, store, or share any of your data. Ever.</p>
            </div>
            <div class="card">
                <h3>What platforms do you support?</h3>
                <p>Windows, macOS, Linux, Android, iOS, and PhazeOS.</p>
            </div>
            <div class="card">
                <h3>How fast is PhazeVPN?</h3>
                <p>Our custom protocol is optimized for speed with minimal overhead.</p>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
    </footer>
</body>
</html>
EOF

# Contact Page
cat > contact.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact - PhazeVPN</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <div class="container">
            <a href="/" class="logo">🔒 PhazeVPN</a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/login" class="btn-secondary">Login</a>
            </div>
        </div>
    </nav>
    <main>
        <div class="auth-container">
            <div class="auth-box">
                <h2>Contact Us</h2>
                <form method="POST">
                    <input type="text" name="name" placeholder="Your Name" required>
                    <input type="email" name="email" placeholder="Your Email" required>
                    <textarea name="message" placeholder="Your Message" rows="5" style="width: 100%; padding: 1.2rem; margin-bottom: 1.5rem; background: rgba(255, 255, 255, 0.05); border: 2px solid rgba(0, 212, 255, 0.2); border-radius: 15px; color: white;" required></textarea>
                    <button type="submit" class="btn-primary btn-block">Send Message</button>
                </form>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
    </footer>
</body>
</html>
EOF

# Create remaining pages with basic content
for page in terms privacy transparency phazebrowser os blog testimonials; do
    cat > ${page}.html << EOFPAGE
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${page^} - PhazeVPN</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <div class="container">
            <a href="/" class="logo">🔒 PhazeVPN</a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/login" class="btn-secondary">Login</a>
            </div>
        </div>
    </nav>
    <main>
        <div class="dashboard" style="max-width: 900px;">
            <h1>${page^}</h1>
            <div class="card">
                <p>Content coming soon...</p>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
    </footer>
</body>
</html>
EOFPAGE
done

echo "✅ All pages created!"
