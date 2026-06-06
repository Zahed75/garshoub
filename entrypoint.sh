#!/bin/bash

set -e

echo "========================================="
echo "Odoo Production Deployment Starting..."
echo "========================================="

# Wait for database to be ready
echo "Waiting for database connection..."
until pg_isready -h ${DB_HOST:-db} -p 5432 -U ${DB_USER:-odoo}; do
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
            -d ${DB_NAME:-flowllet} \
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
        -d ${DB_NAME:-flowllet} \
        -i base,web,mail,crm,raptron_admin \
        --stop-after-init
    
    # Create marker file
    touch /var/lib/odoo/.initialized
    echo "Initialization completed!"
fi

# Clean old assets on every startup
rm -rf /var/lib/odoo/assets-*

echo "========================================="
echo "Starting Odoo server..."
echo "========================================="

# Execute the main command
exec "$@"