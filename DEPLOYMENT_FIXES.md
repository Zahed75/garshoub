# Deployment Fixes — June 2026

## Issues Fixed

### 1. ❌ Broken CSS / Assets on `https://erp.garshoub.com`
**Root Cause:**
- `raptron_admin` module was **not installed** in the database, so the `ir_http.py` redirect (`/` → `/web`) never fired
- Without the redirect, the **website module** served its homepage on `erp.garshoub.com`
- `web.base.url` was either unset or pointing to `http://...`, causing browsers to block mixed-content assets
- aaPanel/nginx was **not sending** `X-Forwarded-Proto: https` to Odoo

**Fixes applied:**
- `entrypoint.sh` now uses `--init=raptron_admin --update=raptron_admin` so the module is **installed if missing** and **updated on every startup**
- `entrypoint.sh` now enforces `web.base.url = https://erp.garshoub.com` and `web.base.url.freeze = 1` on every startup
- `nginx/` configs added with proper `X-Forwarded-*` headers
- `models/res_users.py` cron now also enforces `web.base.url` and `web.base.url.freeze` every 5 minutes

### 2. ❌ Custom Login Screen Not Showing
**Root Cause:**
- `raptron_admin` module was **not installed**, so the login template overrides (`garshoub_login_layout`) were never loaded
- `post_init_hook` referenced a non-existent view `garshoub_website_login_layout` (bug)

**Fixes applied:**
- `entrypoint.sh` now installs the module on startup (see above)
- `odoo/addons/raptron_admin/__init__.py` fixed to reference the correct view ID `garshoub_login_layout`

### 3. ❌ `deploy.sh` Destroyed Data
**Root Cause:**
- `deploy.sh` ran `docker-compose down -v`, which **destroys Docker volumes** (database + filestore)

**Fix applied:**
- Changed to `docker-compose down` (no `-v`) so database and filestore are preserved

### 4. ❌ Website Domain Confusion
**Root Cause:**
- The website's `domain` field was set to `erp.garshoub.com` or empty, causing Odoo to serve the public site on the ERP subdomain

**Fixes applied:**
- `entrypoint.sh` now forces website domain = `garshoub.com`
- `models/res_users.py` cron forces website domain = `garshoub.com` every 5 minutes
- `ir_http.py` redirects `erp.garshoub.com/` → `/web` (works once module is installed)

---

## Files Changed

| File | Change |
|------|--------|
| `entrypoint.sh` | Install+update raptron_admin; enforce web.base.url & freeze; enforce website domain |
| `odoo/addons/raptron_admin/__init__.py` | Fixed non-existent view reference `garshoub_website_login_layout` → `garshoub_login_layout` |
| `odoo/addons/raptron_admin/models/res_users.py` | Added `web.base.url` + `web.base.url.freeze` enforcement to cron; fixed website domain logic |
| `deploy.sh` | Removed `-v` flag from `docker-compose down` |
| `odoo.conf` | Added `local_data/addons/19.0` to `addons_path` |
| `nginx/erp.garshoub.com.conf` | **New** — reverse proxy with proper `X-Forwarded-*` headers |
| `nginx/garshoub.com.conf` | **New** — reverse proxy with proper `X-Forwarded-*` headers |
| `nginx/README.md` | **New** — instructions for applying nginx configs in aaPanel |

---

## Next Steps to Deploy

### Step 1 — Apply nginx configs (MOST IMPORTANT)
Without this, assets will still be broken even after the code fixes.

1. Open **aaPanel** → Website → `erp.garshoub.com` → Config tab
2. Paste the contents of `nginx/erp.garshoub.com.conf`
3. Adjust SSL paths if needed (aaPanel usually auto-injects them)
4. Save & reload nginx
5. Repeat for `garshoub.com` using `nginx/garshoub.com.conf`

See `nginx/README.md` for full instructions.

### Step 2 — Commit & Push
```bash
git add .
git commit -m "fix: install raptron_admin on startup, enforce base URL, add nginx configs, fix deploy script"
git push origin production
```

### Step 3 — Deploy via CI/CD
The GitHub Actions workflow (`.github/workflows/deploy.yml`) will automatically deploy to production when you push to the `production` branch.

Or manually on the server:
```bash
cd /www/wwwroot/garshoub-prod  # or wherever your project lives
git pull origin production
docker compose down
docker compose build --no-cache
docker compose up -d
docker logs -f odoo_app
```

### Step 4 — Verify
After deployment, check:
1. `https://erp.garshoub.com` → should redirect to `/web` and show the **custom Al Garshoub login**
2. `https://garshoub.com` → should show the public website **with CSS**
3. Login page should have the green/gold custom styling

---

## Why `proxy_mode = True` + nginx headers matter

When `proxy_mode = True`, Odoo trusts the `X-Forwarded-*` headers to build URLs. If nginx doesn't send `X-Forwarded-Proto: https`, Odoo thinks the request is HTTP and generates `http://` URLs for assets. Modern browsers block these on HTTPS pages → broken CSS.

**Before (broken):**
```nginx
# ❌ Missing headers
location / {
    proxy_pass http://127.0.0.1:8069;
}
```

**After (fixed):**
```nginx
# ✅ Correct headers
location / {
    proxy_pass http://127.0.0.1:8069;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host  $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
}
```

---

## Troubleshooting

### Still no CSS after deploy?
1. Hard-refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Check container logs: `docker logs -f odoo_app`
3. Verify nginx config: `nginx -t`
4. Check if `web.base.url` is correct in Odoo: Settings → Technical → System Parameters

### Login still shows default Odoo?
1. Make sure `raptron_admin` shows as **Installed** in Apps
2. Go to Settings → Technical → Views → search `garshoub_login_layout` → ensure it exists
3. Restart the container to trigger entrypoint again
