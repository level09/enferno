# Deployment Guide

This guide covers deploying Enferno in production environments using Docker or traditional deployment methods.

## Production Checklist

Before deploying:

1. Set secure environment variables
2. Configure proper database settings
3. Enable HTTPS
4. Set up monitoring
5. Configure backups
6. Set up logging

## Docker Deployment

### Prerequisites

- Docker
- Docker Compose
- Domain name
- SSL certificate

### Quick Start

1. Clone and setup:
```bash
git clone git@github.com:level09/enferno.git
cd enferno
./setup.sh  # Creates Python environment and secure .env
# Edit .env with production settings
```

2. Build and run:
```bash
docker compose up --build
```

3. Initialize database:
```bash
docker compose exec website flask create-db
docker compose exec website flask install
```

## Traditional Deployment

### Prerequisites

- Python 3.11+
- Redis
- PostgreSQL
- Nginx
- Domain name
- SSL certificate

### System Setup

1. Install system dependencies:
```bash
# Ubuntu/Debian
apt-get update
apt-get install build-essential python3-dev libjpeg8-dev \
    libzip-dev libffi-dev libxslt1-dev python3-pip \
    libpq-dev postgresql postgresql-contrib git \
    redis-server python3-venv nginx certbot python3-certbot-nginx
```

2. Create application user:
```bash
# Create user and group
useradd -m -s /bin/bash enferno
usermod -aG sudo enferno

# Set up SSH keys for the user
mkdir -p /home/enferno/.ssh
cp ~/.ssh/authorized_keys /home/enferno/.ssh/
chown -R enferno:enferno /home/enferno/.ssh
chmod 700 /home/enferno/.ssh
chmod 600 /home/enferno/.ssh/authorized_keys
```

### Application Setup

1. Clone and configure:
```bash
su - enferno
git clone git@github.com:level09/enferno.git /home/enferno/your-domain.com
cd /home/enferno/your-domain.com
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
./generate-env.sh  # Creates .env file with secure keys
# Edit .env with production settings
```

3. Initialize database:
```bash
flask create-db
flask install
```

### System Services

#### uWSGI Service Configuration

Create `/etc/systemd/system/enferno.service`:

```ini
[Unit]
Description=uWSGI instance for Flask Enferno Application
After=network.target

[Service]
User=enferno
Group=enferno
WorkingDirectory=/home/enferno/your-domain.com
Environment="FLASK_DEBUG=0"
ExecStart=/home/enferno/your-domain.com/env/bin/uwsgi \
    --master \
    --enable-threads \
    --threads 2 \
    --processes 4 \
    --http 127.0.0.1:8000 \
    --worker-reload-mercy 30 \
    --reload-mercy 30 \
    -w run:app \
    --home env
Restart=always
Type=notify
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/clry.service`:
```ini
[Unit]
Description=Celery Worker for Enferno
After=network.target

[Service]
User=enferno
Group=enferno
WorkingDirectory=/home/enferno/your-domain.com
Environment="FLASK_DEBUG=0"
ExecStart=/home/enferno/your-domain.com/env/bin/celery -A enferno.tasks worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
systemctl enable enferno clry
systemctl start enferno clry
```

#### Nginx Configuration

1. Remove default config:
```bash
rm /etc/nginx/conf.d/default.conf
```

2. Create `/etc/nginx/nginx.conf`:
```nginx
user enferno;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 2048;

    # Rate limiting for POST requests
    map $request_method $limit {
        default         "";
        POST            $binary_remote_addr;
    }
    limit_req_zone $limit zone=post_limit:10m rate=1r/s;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # SSL Settings
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

3. Set up SSL:
```bash
# Create webroot directory
mkdir -p /var/www/html/.well-known/acme-challenge

# Obtain SSL certificate
certbot certonly --webroot -w /var/www/html -d your-domain.com --non-interactive --agree-tos --email your-email@domain.com

# Set up auto-renewal
echo "0 0 * * * certbot renew --quiet --no-self-upgrade && systemctl reload nginx" > /etc/cron.d/certbot
```

### Firewall Setup

```bash
# Enable UFW
ufw enable

# Allow essential ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
```

### Monitoring

1. Application logs:
```bash
journalctl -u enferno.service
```

2. Nginx logs:
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Backup Strategy

1. Database backup:
```bash
pg_dump enferno > backup.sql
```

2. Redis backup:
```bash
redis-cli save
```

3. Application files:
```bash
tar -czf backup.tar.gz uploads/ .env
```

## Monitoring

### Application Monitoring

- Use Flask Debug Toolbar in development
- Configure logging
- Set up error tracking (e.g., Sentry)
- Monitor application metrics

### System Monitoring

- Monitor system resources
- Set up log rotation
- Configure backup systems
- Monitor security events

## Security Considerations

1. Enable security headers in Nginx
2. Configure firewall rules
3. Set up fail2ban
4. Regular security updates
5. Monitor authentication logs
6. Implement rate limiting
7. Regular security audits 