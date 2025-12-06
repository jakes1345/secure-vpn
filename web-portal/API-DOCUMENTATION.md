# PhazeVPN Web Portal API Documentation

## Base URL
```
https://phazevpn.com
```

## Authentication

Most endpoints require authentication via session cookie. Some endpoints support API token authentication.

### Session Authentication
- Login via `/login` endpoint
- Session cookie is set automatically
- Session expires after 8 hours

### API Token Authentication (Future)
- Token-based authentication for API clients
- Header: `Authorization: Bearer <token>`

## Endpoints

### Health & Status

#### GET `/health`
Comprehensive health check of all services.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy", "timestamp": "..."},
    "disk_space": {"status": "healthy", "used_percent": 45.2, ...},
    "vpn_service": {"status": "healthy", "active": true, ...},
    "web_portal": {"status": "healthy", ...},
    "system": {"platform": "Linux", ...}
  },
  "timestamp": "2025-01-20T12:00:00"
}
```

**Status Codes:**
- `200` - Healthy or degraded
- `503` - Unhealthy

#### GET `/health/database`
Database connection health check.

#### GET `/health/disk`
Disk space health check.

#### GET `/health/vpn`
VPN service health check.

#### GET `/api/status`
Basic API status.

**Response:**
```json
{
  "status": "operational",
  "service": "PhazeVPN Web Portal",
  "version": "1.0.0",
  "timestamp": "2025-01-20T12:00:00"
}
```

### Authentication

#### POST `/login`
User login.

**Request:**
```json
{
  "username": "user123",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "redirect": "/dashboard"
}
```

**Errors:**
- `400` - Invalid input
- `401` - Invalid credentials
- `429` - Rate limit exceeded

#### POST `/signup`
User registration.

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepass123",
  "confirm_password": "securepass123"
}
```

**Validation:**
- Username: 3-30 chars, alphanumeric + underscore/hyphen
- Email: Valid email format
- Password: Min 8 chars, letters and numbers

**Response:**
```json
{
  "success": true,
  "message": "Account created. Please verify your email."
}
```

#### POST `/api/profile/password`
Change password.

**Request:**
```json
{
  "current_password": "oldpass123",
  "new_password": "newpass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

### VPN Clients

#### POST `/api/clients`
Create new VPN client.

**Request:**
```json
{
  "name": "my-client",
  "protocol": "openvpn"
}
```

**Validation:**
- Client name: 1-50 chars, alphanumeric + underscore/hyphen
- Protocol: openvpn, wireguard, or phazevpn

**Response:**
```json
{
  "success": true,
  "client_name": "my-client",
  "config_url": "/download/client/my-client"
}
```

#### DELETE `/api/clients/<client_name>`
Delete VPN client.

**Response:**
```json
{
  "success": true,
  "message": "Client deleted successfully"
}
```

#### POST `/api/vpn/connect`
Connect to VPN.

**Request:**
```json
{
  "client_name": "my-client",
  "protocol": "openvpn"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connecting to VPN..."
}
```

### Support Tickets

#### POST `/api/tickets`
Create support ticket.

**Request:**
```json
{
  "subject": "VPN connection issue",
  "message": "I'm having trouble connecting...",
  "email": "user@example.com"
}
```

**Validation:**
- Subject: 3-200 chars
- Message: 10-5000 chars
- Email: Valid email format (optional)

**Response:**
```json
{
  "success": true,
  "ticket_id": "TICKET-ABC123",
  "ticket": {...}
}
```

#### POST `/api/tickets/<ticket_id>/reply`
Reply to ticket.

**Request:**
```json
{
  "message": "Thank you for the update..."
}
```

**Validation:**
- Message: 10-5000 chars

**Response:**
```json
{
  "success": true,
  "message": "Reply added successfully"
}
```

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": "Error message here"
}
```

### Common Error Codes

- `400` - Bad Request (validation error)
- `401` - Unauthorized (not authenticated)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting

- Rate limits are applied per username (privacy-friendly)
- Default: 5 requests per 15 minutes per endpoint
- Rate limit headers:
  - `X-RateLimit-Limit`: Maximum requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

## Security

- All POST endpoints validate CSRF tokens (when Flask-WTF available)
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)
- Security headers on all responses

## Privacy

- No IP address tracking
- No connection history logging
- Username-only rate limiting
- System-error-only logging
- Zero user activity tracking
