# Authentication

Enferno provides comprehensive authentication features through Flask-Security-Too, including OAuth integration, two-factor authentication, and WebAuthn support.

## Built-in Authentication

### User Registration

Users can register through:

- Traditional email/password registration
- OAuth providers (Google, GitHub)
- WebAuthn (passwordless)

### Password Policies

Default security settings:
```python
SECURITY_PASSWORD_LENGTH_MIN = 9
SECURITY_PASSWORD_COMPLEXITY_CHECKER = 'zxcvbn'
SECURITY_TWO_FACTOR = True
SECURITY_TRACKABLE = True
```

### Two-Factor Authentication (2FA)

Supported methods:

- Authenticator apps (TOTP)
- WebAuthn devices
- Recovery codes

## OAuth Integration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the Google+ API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials
6. Add authorized redirect URI: `http://your-domain/login/google/authorized`

Configure in `.env`:
```bash
GOOGLE_AUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
```

### GitHub OAuth Setup

1. Go to GitHub Settings > Developer Settings > OAuth Apps
2. Create New OAuth App
3. Set Homepage URL to your domain
4. Set Authorization callback URL: `http://your-domain/login/github/authorized`

Configure in `.env`:
```bash
GITHUB_AUTH_ENABLED=true
GITHUB_OAUTH_CLIENT_ID=your_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret
```

## WebAuthn Support

WebAuthn enables passwordless authentication using security keys or biometric authentication.

### Configuration

```python
SECURITY_WEBAUTHN = True
SECURITY_WAN_ALLOW_AS_FIRST_FACTOR = True
SECURITY_WAN_ALLOW_AS_MULTI_FACTOR = True
```

### Usage

1. Users register their WebAuthn device (security key, fingerprint, etc.)
2. Can be used as primary or secondary authentication factor
3. Multiple devices can be registered per user

## Session Management

Security settings for sessions:
```python
SESSION_TYPE = 'redis'
SESSION_PROTECTION = "strong"
SESSION_USE_SIGNER = True
PERMANENT_SESSION_LIFETIME = 3600
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

## Role-Based Access Control

### Default Roles

- Admin: Full system access
- User: Standard user access
- Custom roles can be created

### Usage Example

```python
@roles_required('admin')
def admin_view():
    pass

@roles_accepted('admin', 'editor')
def editor_view():
    pass
```

## Email Configuration

For password reset and email verification:

```bash
MAIL_SERVER=smtp.example.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
SECURITY_EMAIL_SENDER=noreply@example.com
```

## Security Best Practices

1. Always use HTTPS in production
2. Keep security dependencies updated
3. Enable 2FA for admin accounts
4. Regularly audit user access
5. Monitor authentication logs
6. Use strong password policies
7. Implement rate limiting for auth endpoints 