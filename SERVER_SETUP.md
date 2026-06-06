# Server Setup Guide

## Required GitHub Secrets

Go to **Settings > Secrets and variables > Actions** and add:

### Development Server (hq.flowllet.com)
- `DEV_SSH_HOST` = `103.191.51.220`
- `DEV_SSH_USER` = your SSH username
- `DEV_SSH_KEY` = your private SSH key
- `DEV_DB_NAME` = `flowllet` (optional, defaults to flowllet)
- `DEV_DB_USER` = `odoo` (optional, defaults to odoo)

### Production Server (hq.syscomatic.com)
- `PROD_SSH_HOST` = `156.67.216.209`
- `PROD_SSH_USER` = your SSH username
- `PROD_SSH_KEY` = your private SSH key
- `PROD_DB_NAME` = `odoo` (optional, defaults to odoo)
- `PROD_DB_USER` = `odoo` (optional, defaults to odoo)

## Server Environment Files

On each server, create a `.env` file in the project root:

### Development (.env)
```bash
DB_USER=odoo
DB_PASSWORD=Sysc@2@26#
DB_NAME=flowllet
ODOO_PORT=8069
```

### Production (.env)
```bash
DB_USER=odoo
DB_PASSWORD=Sysc@2@26#
DB_NAME=odoo
ODOO_PORT=8069
```

## Nginx Reverse Proxy (Required)

For Odoo to work correctly, especially WebSockets for real-time features (chat, online status, notifications), use this nginx configuration:

```nginx
upstream odoo {
    server 127.0.0.1:8069;
}

upstream odoo_websocket {
    server 127.0.0.1:8072;
}

server {
    listen 80;
    server_name hq.syscomatic.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hq.syscomatic.com;

    # SSL Configuration (use certbot or your certificates)
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;

    client_max_body_size 200M;

    location / {
        proxy_pass http://odoo;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_redirect off;
    }

    # WebSocket support - CRITICAL for online status and notifications
    # MUST proxy to port 8072 (Odoo websocket port), NOT 8069
    location /websocket {
        proxy_pass http://127.0.0.1:8072;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Longpolling fallback (Odoo 16 and earlier)
    location /longpolling {
        proxy_pass http://odoo_websocket;
    }

    location ~* /web/static/ {
        proxy_cache_valid 200 90m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://odoo;
    }
}
```

### For Development Server (hq.flowllet.com)
Replace `server_name` with `hq.flowllet.com`.

## Important Notes

1. **Data Safety**: The CI/CD pipeline creates automatic database backups before each deployment in the `./backups/` folder.

2. **WebSocket Requirement**: Without the `/websocket` location block in nginx, users will always appear offline and real-time chat/notifications will not work.

3. **Module Updates**: The `entrypoint.sh` automatically detects changes in `raptron_admin` and updates the module on container restart. For other modules, manual update via UI or command line is required.

4. **Database Names**: 
   - Production uses database `odoo`
   - Development uses database `flowllet`
   
   These are controlled by the `DB_NAME` environment variable.
