from . import models
from . import controllers

def post_init_hook(env):
    # 1. Reset Admin Credentials
    # Search by any known old login
    admin = env['res.users'].search([
        '|', '|',
        ('login', '=', 'admin'),
        ('login', '=', 'tech.syscomatic@gmail.com'),
        ('id', '=', env.ref('base.user_admin').id)
    ], limit=1, order='id desc')
    if admin:
        admin.write({
            'login': 'fgarshoub@gmail.com',
            'password': 'G@rsh@ub2@26',
        })

    # 2. Configure SMTP
    Smtp = env['ir.mail_server']
    if not Smtp.search([('name', '=', 'Syscomatic Gmail SMTP')]):
        Smtp.create({
            'name': 'Garshoub Gmail SMTP',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': 'fgarshoub@gmail.com',
            'smtp_pass': 'ythx yyrf dtwc zdni',
            'smtp_encryption': 'starttls',
            'from_filter': 'fgarshoub@gmail.com',
            'sequence': 1,
        })

    # 3. Force Expiration
    env['ir.config_parameter'].sudo().set_param('database.expiration_date', '2099-12-31 23:59:59')

    # 4. Ensure our login template has highest priority
    # This prevents other modules (like website) from overriding our custom login
    login_template = env['ir.ui.view'].search([
        ('xml_id', '=', 'raptron_admin.garshoub_login_layout')
    ], limit=1)
    if login_template:
        # Bump priority to ensure it wins over website_login_layout etc.
        login_template.write({'priority': 1})
        env.cr.commit()

    # 5. Ensure web_layout (favicon) also has high priority
    layout_template = env['ir.ui.view'].search([
        ('xml_id', '=', 'raptron_admin.garshoub_web_favicon')
    ], limit=1)
    if layout_template:
        layout_template.write({'priority': 1})
        env.cr.commit()
