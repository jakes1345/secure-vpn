# Quick Start Guide - Using the Improved Code

## Installation

No additional installation needed! All improvements use existing dependencies.

## Basic Usage Examples

### 1. Configuration

```python
from web-portal.config import Config, get_config

# Get production config
config = get_config('production')

# Access settings
print(config.VPN_SERVER_IP)
print(config.DB_CONFIG_FILE)
```

### 2. Logging

```python
from web-portal.logging_config_improved import setup_logging, get_logger

# Setup logging (do this once at app start)
setup_logging(log_level='INFO')

# Get logger for your module
logger = get_logger(__name__)

# Use it
logger.info("User logged in successfully")
logger.error("Failed to connect to database")
logger.debug("Processing request data: %s", data)
```

### 3. Email Service

```python
from web-portal.services.email_service import get_email_service

# Get email service
email_service = get_email_service()

# Send welcome email
result = email_service.send_welcome_email(
    username='john',
    email='john@example.com'
)

# Send custom email
result = email_service.send_email(
    to_email='user@example.com',
    subject='Important Notice',
    html_body='<h1>Hello!</h1><p>This is a test email.</p>'
)

print(result)  # {'success': True, 'message': 'Email sent successfully'}
```

### 4. Route Decorators

```python
from flask import Flask, render_template
from web-portal.utils import login_required, admin_required

app = Flask(__name__)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html')
```

### 5. Error Handling

```python
from web-portal.error_handling import (
    ValidationError,
    AuthenticationError,
    register_error_handlers
)

# Register error handlers with Flask app
register_error_handlers(app)

# Use custom exceptions
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    
    if not username:
        raise ValidationError("Username is required", field="username")
    
    # ... rest of signup logic
```

### 6. Utility Functions

```python
from web-portal.utils import (
    hash_password,
    verify_password,
    format_bytes,
    format_duration,
    get_client_ip
)

# Password hashing
hashed = hash_password('my_password')
is_valid = verify_password('my_password', hashed)

# Formatting
print(format_bytes(1024 * 1024))  # "1.00 MB"
print(format_duration(3661))       # "1h 1m"

# Get client IP (handles proxies)
client_ip = get_client_ip()
```

### 7. Input Validation

```python
from web-portal.utils import (
    validate_username,
    validate_email,
    validate_password,
    sanitize_input
)

# Validate input
is_valid, error = validate_username('john123')
if not is_valid:
    print(f"Error: {error}")

is_valid, error = validate_email('user@example.com')
if not is_valid:
    print(f"Error: {error}")

# Sanitize input
clean_input = sanitize_input(user_input, max_length=100)
```

## Integration with Existing Code

### Update app.py (Recommended)

```python
# At the top of app.py, add:
from web-portal.config import Config
from web-portal.logging_config_improved import setup_logging, get_logger
from web-portal.error_handling import register_error_handlers
from web-portal.utils import login_required, admin_required

# Setup logging
setup_logging(log_level=Config.LOG_LEVEL)
logger = get_logger(__name__)

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Register error handlers
register_error_handlers(app)

# Now use the new utilities in your routes
@app.route('/dashboard')
@login_required
def dashboard():
    logger.info(f"User {session['username']} accessed dashboard")
    return render_template('dashboard.html')
```

## Testing

```bash
# Test logging
cd /home/ubuntu/secure-vpn
python3 web-portal/logging_config_improved.py

# Test configuration
python3 -c "from web-portal.config import Config; print(f'VPN Server: {Config.VPN_SERVER_IP}')"

# Test email service (requires email configuration)
python3 -c "from web-portal.services.email_service import send_email; print(send_email('test@example.com', 'Test', '<h1>Test</h1>'))"
```

## Environment Variables

Set these for production:

```bash
# Flask
export FLASK_ENV=production
export FLASK_SECRET_KEY='your-secret-key-here'

# HTTPS
export HTTPS_ENABLED=true

# Email (choose one provider)
export EMAIL_PROVIDER=mailgun
export MAILGUN_API_KEY='your-key'
export MAILGUN_DOMAIN='your-domain'

# Or use SMTP
export EMAIL_PROVIDER=smtp
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER='your-email@gmail.com'
export SMTP_PASSWORD='your-app-password'

# Logging
export LOG_LEVEL=INFO
```

## Common Patterns

### Safe Operations

```python
from web-portal.error_handling import safe_operation

# Automatically handle errors
with safe_operation("Creating user", raise_on_error=False):
    create_user(username, password)
    send_welcome_email(email)
```

### Request Logging

```python
from web-portal.logging_config_improved import log_request, log_response
import time

@app.before_request
def before_request():
    request.start_time = time.time()
    log_request(logger, request)

@app.after_request
def after_request(response):
    duration = (time.time() - request.start_time) * 1000
    log_response(logger, response, duration)
    return response
```

## Tips

1. **Read the docstrings** - Every function has detailed documentation
2. **Check REFACTORING_NOTES.md** - Comprehensive guide to all improvements
3. **Use type hints** - Your IDE will provide better autocomplete
4. **Start small** - Integrate one module at a time
5. **Backward compatible** - Old code still works while you migrate

## Questions?

Check these files:
- `IMPROVEMENTS_SUMMARY.md` - Overview of all improvements
- `REFACTORING_NOTES.md` - Detailed documentation
- `REFACTORING_PLAN.md` - Refactoring strategy
- Module docstrings - In each Python file
