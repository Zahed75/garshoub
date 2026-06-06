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

# Check if this is first run or update needed
if [ -f "/var/lib/odoo/.initialized" ]; then
    echo "Existing installation detected. Checking for updates..."
    UPDATE_MODULES=""
    
    # Check if custom module has changes
    if [ -n "$(find /opt/odoo/odoo/addons/raptron_admin -name '*.py' -newer /var/lib/odoo/.initialized 2>/dev/null)" ] || \
       [ -n "$(find /opt/odoo/odoo/addons/raptron_admin/views -name '*.xml' -newer /var/lib/odoo/.initialized 2>/dev/null)" ] || \
       [ -n "$(find /opt/odoo/odoo/addons/raptron_admin/static -name '*.css' -newer /var/lib/odoo/.initialized 2>/dev/null)" ]; then
        UPDATE_MODULES="raptron_admin"
        echo "Changes detected in raptron_admin module!"
    fi
    
    # Run updates if needed
    if [ -n "$UPDATE_MODULES" ]; then
        echo "Updating modules: $UPDATE_MODULES"
        python3 /opt/odoo/odoo-bin -c /opt/odoo/odoo.conf \
            -d "${DB_NAME:-Garshoub HQ}" \
            --update=$UPDATE_MODULES \
            --stop-after-init
        
        # Clear asset cache (preserve initialization marker)
        echo "Clearing asset cache..."
        rm -rf /var/lib/odoo/assets-*
        
        echo "Module update completed!"
    else
        echo "No changes detected. Skipping update."
    fi
else
    echo "First run detected. Initializing database..."
    
    # First run - update all modules
    python3 /opt/odoo/odoo-bin -c /opt/odoo/odoo.conf \
        -d "${DB_NAME:-Garshoub HQ}" \
        -i base,web,mail,crm,raptron_admin \
        --stop-after-init
    
    # Create marker file
    touch /var/lib/odoo/.initialized
    echo "Initialization completed!"
fi

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