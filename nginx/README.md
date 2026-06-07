# Nginx Reverse Proxy Configuration

## Problem
Odoo behind aaPanel/nginx was missing critical proxy headers, causing:
1. **Broken CSS/JS/assets** on `https://erp.garshoub.com` — browsers block mixed HTTP content on HTTPS pages
2. **Wrong base URL detection** — Odoo couldn't tell the request came through HTTPS

## Solution
Both domain configs now pass these **critical headers**:
```nginx
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host  $host;
proxy_set_header X-Forwarded-Port 443;
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
```

## How to apply in aaPanel

### Option A: Paste via aaPanel UI (Recommended)
1. Open aaPanel → Website → click `erp.garshoub.com`
2. Go to **Config** tab
3. Replace the entire config with the contents of `nginx/erp.garshoub.com.conf`
4. Adjust the SSL certificate paths to match your aaPanel setup
5. Save and reload Nginx
6. Repeat for `garshoub.com` using `nginx/garshoub.com.conf`

### Option B: Manual symlink (if you have SSH access)
```bash
# Backup existing configs first
cp /www/server/panel/vhost/nginx/erp.garshoub.com.conf ~/erp.garshoub.com.conf.bak
cp /www/server/panel/vhost/nginx/garshoub.com.conf ~/garshoub.com.conf.bak

# Copy new configs
cp /path/to/project/nginx/erp.garshoub.com.conf /www/server/panel/vhost/nginx/erp.garshoub.com.conf
cp /path/to/project/nginx/garshoub.com.conf /www/server/panel/vhost/nginx/garshoub.com.conf

# Test and reload nginx
nginx -t
/etc/init.d/nginx reload
```

## SSL Certificates
aaPanel automatically manages SSL via Let's Encrypt. The configs reference:
```nginx
# ssl_certificate /www/server/panel/vhost/cert/DOMAIN/fullchain.pem;
# ssl_certificate_key /www/server/panel/vhost/cert/DOMAIN/privkey.pem;
```
If aaPanel inserts its own SSL directives automatically, you can leave those lines commented out.

## Important
- Both `erp.garshoub.com` and `garshoub.com` must use these headers
- Do **not** forget `X-Forwarded-Proto $scheme` — this is the header that fixes the broken CSS
- `erp.garshoub.com` should proxy to the same Odoo container as `garshoub.com`
