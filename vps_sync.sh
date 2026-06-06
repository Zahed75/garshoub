#!/bin/bash
echo "Starting VPS Sync and Auto-Fix..."

# 1. Pull latest code from GitHub
git pull origin main

# 2. Rebuild and restart containers
docker-compose up -d --build

# 3. Force Module Upgrade (Applies CSS, Welcome Heading, and Email Fixes)
echo "Upgrading raptron_admin module..."
docker exec odoo_app python3 -m odoo --db_host=db --db_user=odoo --db_password=Sysc@2@26# -d flowllet --addons-path=/opt/odoo/odoo/addons -u raptron_admin --stop-after-init

# 4. Force 2099 Expiration Date
echo "Setting expiration date to 2099..."
docker exec odoo_app python3 -m odoo shell --db_host=db --db_user=odoo --db_password=Sysc@2@26# -d flowllet --no-http <<EOF
env['ir.config_parameter'].sudo().set_param('database.expiration_date', '2099-12-31 23:59:59')
env.cr.commit()
EOF

# 5. Final Restart
docker restart odoo_app

echo "VPS Sync Complete! Check hq.syscomatic.com now."
