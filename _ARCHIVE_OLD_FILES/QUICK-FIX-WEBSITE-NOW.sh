#!/bin/bash
# QUICK FIX - Upload base.html and restart Flask

ssh root@15.204.11.19 << 'EOF'
cd /opt/secure-vpn/web-portal/templates
cat > base.html << 'BASEEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}PhazeVPN - Military-Grade VPN Protection{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <div class="navbar-container">
            <a href="{{ url_for('index') }}" class="navbar-brand">🔒 PhazeVPN</a>
            <div class="navbar-nav">
                {% if session.get('username') %}
                    <a href="{{ url_for('dashboard') }}">Dashboard</a>
                    <a href="{{ url_for('profile') }}">Profile</a>
                    <a href="{{ url_for('logout') }}">Logout</a>
                {% else %}
                    <a href="{{ url_for('index') }}">Home</a>
                    <a href="{{ url_for('download_page') }}">Download</a>
                    <a href="{{ url_for('guide') }}">Guide</a>
                    <a href="{{ url_for('login') }}">Login</a>
                    <a href="{{ url_for('signup') }}">Sign Up</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <main style="flex: 1;">
        {% block content %}{% endblock %}
    </main>
    <footer class="footer">
        <p>&copy; 2025 PhazeVPN. All rights reserved.</p>
    </footer>
    {% block extra_js %}{% endblock %}
</body>
</html>
BASEEOF

pkill -9 -f 'python.*app.py'
cd /opt/secure-vpn/web-portal
nohup python3 app.py > /tmp/flask-app.log 2>&1 &
sleep 2
curl -s http://127.0.0.1:5000/ | head -5
EOF

echo "✅ Website fixed!"

