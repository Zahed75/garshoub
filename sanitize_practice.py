from datetime import datetime, timedelta
future_date = (datetime.now() + timedelta(days=3650)).strftime('%Y-%m-%d %H:%M:%S')

# Sanitize Master DB
registry = odoo.orm.registry.Registry('odooZayanori')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    env['ir.config_parameter'].sudo().set_param('database.expiration_date', future_date)
    env['ir.config_parameter'].sudo().set_param('database.expiration_reason', 'none')
    cron = env.ref('base.ir_cron_publisher_warranty_contract', raise_if_not_found=False)
    if cron: cron.active = False
    cr.commit()

# Sanitize Asif DB
try:
    client_registry = odoo.orm.registry.Registry('Asif Undergarments')
    with client_registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        env['ir.config_parameter'].sudo().set_param('database.expiration_date', future_date)
        env['ir.config_parameter'].sudo().set_param('database.expiration_reason', 'none')
        cron = env.ref('base.ir_cron_publisher_warranty_contract', raise_if_not_found=False)
        if cron: cron.active = False
        cr.commit()
except Exception:
    pass

print("PRACTICE_SANITIZED")
