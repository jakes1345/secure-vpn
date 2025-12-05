# SecureVPN Web Portal

Modern web-based admin, moderator, and user dashboards.

## Features

✅ **Admin Panel**
- VPN start/stop/restart
- Client management (add, edit, delete)
- User management
- Server settings
- Logs viewing
- Statistics

✅ **Moderator Panel**
- Client management
- Support portal
- View logs
- Export configs

✅ **User Dashboard**
- View VPN status
- Download configs
- View statistics

✅ **Security**
- Role-based access control (RBAC)
- Session management
- Password hashing
- Permission checks

## Installation

```bash
cd web-portal
pip3 install -r requirements.txt
```

## Running

```bash
python3 app.py
```

Then visit: http://localhost:5000

## Default Logins

- **Admin:** `admin` / `admin123`
- **Moderator:** `moderator` / `mod123`
- **User:** `user` / `user123`

⚠️ **Change these passwords immediately!**

## Ports

- Web Portal: `5000` (default)
- Download Server: `8081`
- VPN Server: `1194`

## Structure

```
web-portal/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── admin/
│   ├── moderator/
│   └── user/
└── README.md
```

## API Endpoints

- `GET /api/vpn/status` - Get VPN status
- `POST /api/vpn/start` - Start VPN
- `POST /api/vpn/stop` - Stop VPN
- `GET /api/clients` - List clients
- `POST /api/clients` - Add client
- `DELETE /api/clients/<name>` - Delete client
- `GET /api/users` - List users
- `POST /api/users` - Add user
- `DELETE /api/users/<username>` - Delete user

