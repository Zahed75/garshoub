# 1. Update the mapping in master DB
registry = odoo.orm.registry.Registry('odooZayanori')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    # Check if mapping exists
    client = env['saas.client'].search([('admin_email', '=', '16i23y58gr@ozsaip.com')], limit=1)
    if not client:
        env['saas.client'].create({
            'name': 'Asif Undergarments',
            'db_name': 'Asif Undergarments',
            'admin_email': '16i23y58gr@ozsaip.com'
        })
    cr.commit()

# 2. Update the admin user in the client DB
client_registry = odoo.orm.registry.Registry('Asif Undergarments')
with client_registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    user = env.ref('base.user_admin')
    user.write({'login': '16i23y58gr@ozsaip.com', 'password': 'test@123'})
    cr.commit()
print("ASIF_FIXED")
