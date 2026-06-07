#!/bin/bash

set -e

echo "========================================="
echo "Odoo Production Deployment Starting..."
echo "========================================="

# Wait for database to be ready
echo "Waiting for database connection..."
until pg_isready -h "${DB_HOST:-db}" -p 5432 -U "${DB_USER:-odoo}"; do
    echo "Database is unavailable - sleeping"
    sleep 2
done
echo "Database is ready!"

# ALWAYS ensure raptron_admin is installed and up-to-date on every startup
# --init installs if missing, --update applies changes if already installed
echo "Installing / Updating raptron_admin module..."
python3 /opt/odoo/odoo-bin -c /opt/odoo/odoo.conf \
    -d "${DB_NAME:-garshoub_hq}" \
    --init=raptron_admin \
    --update=raptron_admin \
    --stop-after-init || echo "Module update failed, continuing to start server..."

# Enforce correct base URL and website domain settings
echo "Enforcing base URL and website domain settings..."
python3 -c "
import os, odoo
db = os.environ.get('DB_NAME', 'garshoub_hq')
try:
    odoo.tools.config.parse_config(['-c', '/opt/odoo/odoo.conf'])
    registry = odoo.registry(db)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # 1. Freeze web.base.url to erp.garshoub.com so assets generate correctly
        param = env['ir.config_parameter'].sudo()
        param.set_param('web.base.url', 'https://erp.garshoub.com')
        param.set_param('web.base.url.freeze', '1')
        print('[entrypoint] web.base.url set to https://erp.garshoub.com (frozen)')
        
        # 2. Ensure website domain is garshoub.com (public site), not erp.garshoub.com
        Website = env['website'].sudo()
        for website in Website.search([]):
            if website.domain != 'garshoub.com':
                website.write({'domain': 'garshoub.com'})
                print(f'[entrypoint] Website {website.id} domain set to garshoub.com')
        
        env.cr.commit()
        print('[entrypoint] URL settings enforced successfully')
except Exception as e:
    print(f'[entrypoint] URL enforcement warning: {e}')
" || echo "URL enforcement skipped"

# Clear asset cache to force fresh CSS/JS bundles
echo "Clearing asset cache..."
rm -rf /var/lib/odoo/assets-*

# Create/update initialization marker
touch /var/lib/odoo/.initialized
echo "Module update completed!"

# Update admin user credentials from code (runs on EVERY startup)
echo "Updating admin credentials..."
python3 -c "
import os, odoo
db = os.environ.get('DB_NAME', 'garshoub_hq')
try:
    odoo.tools.config.parse_config(['-c', '/opt/odoo/odoo.conf'])
    registry = odoo.registry(db)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # 1. Update base.user_admin
        admin = env.ref('base.user_admin')
        admin.write({'login': 'fgarshoub@gmail.com', 'password': 'G@rsh@ub2@26'})
        print(f'[entrypoint] base.user_admin updated: login={admin.login}')
        
        # 2. Also find and update ANY user with the old login
        old_users = env['res.users'].search([
            '|',
            ('login', '=', 'tech.syscomatic@gmail.com'),
            ('login', '=', 'admin')
        ])
        for old in old_users:
            if old.id != admin.id:
                old.write({'login': 'fgarshoub@gmail.com', 'password': 'G@rsh@ub2@26'})
                print(f'[entrypoint] Old user {old.id} updated to new credentials')
        
        env.cr.commit()
        print('[entrypoint] Admin credentials updated successfully')
except Exception as e:
    print(f'[entrypoint] Admin update warning: {e}')
" || echo "Admin update skipped"

# Clean old assets on every startup
rm -rf /var/lib/odoo/assets-*

echo "========================================="
echo "Starting Odoo server..."
echo "========================================="

# Execute the main command
exec "$@"
