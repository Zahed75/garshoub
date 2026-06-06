import sys
import odoo

odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'odooZayanori'])
registry = odoo.registry('odooZayanori')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    user = env.ref('base.user_admin')
    user.write({
        'login': 'zayanori.business@gmail.com',
        'password': 'Z@y@nori2@26#'
    })
    env.cr.commit()
    print("Admin user updated successfully.")
