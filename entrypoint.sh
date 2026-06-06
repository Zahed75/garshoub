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

# ALWAYS update raptron_admin on every startup
# This ensures template/CSS changes are applied without manual intervention
echo "Updating raptron_admin module..."
python3 /opt/odoo/odoo-bin -c /opt/odoo/odoo.conf \
    -d "${DB_NAME:-Garshoub HQ}" \
    --update=raptron_admin \
    --stop-after-init

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
db = os.environ.get('DB_NAME', 'Garshoub HQ')
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
