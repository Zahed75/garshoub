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
    try:
        login_template = env.ref('raptron_admin.garshoub_login_layout', raise_if_not_found=False)
        if login_template:
            login_template.write({'priority': 30})
            env.cr.commit()
    except Exception:
        pass

    # 5. Ensure web_layout (favicon) also has high priority
    try:
        layout_template = env.ref('raptron_admin.garshoub_web_favicon', raise_if_not_found=False)
        if layout_template:
            layout_template.write({'priority': 1})
            env.cr.commit()
    except Exception:
        pass

    # 6. Ensure website.login_layout keeps its default priority=20
    # Our garshoub_login_layout (priority=30) will apply AFTER it and replace website.layout
    try:
        website_login_override = env.ref('website.login_layout', raise_if_not_found=False)
        if website_login_override and website_login_override.priority != 20:
            website_login_override.write({'priority': 20})
            env.cr.commit()
    except Exception:
        pass
