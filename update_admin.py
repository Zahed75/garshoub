#!/usr/bin/env python3
"""
Update admin user credentials on every startup.
This is idempotent — safe to run multiple times.
"""
import os
import odoo

db_name = os.environ.get('DB_NAME', 'Garshoub HQ')
admin_login = os.environ.get('ADMIN_LOGIN', 'fgarshoub@gmail.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'G@rsh@ub2@26')

try:
    odoo.tools.config.parse_config(['-c', '/opt/odoo/odoo.conf'])
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        user = env.ref('base.user_admin')
        user.write({
            'login': admin_login,
            'password': admin_password,
        })
        env.cr.commit()
        print(f"[update_admin] Admin user updated to {admin_login}")
except Exception as e:
    print(f"[update_admin] Warning: {e}")
