{
    'name': 'Raptron Admin Portal',
    'version': '19.0.1.0.0',
    'summary': 'Standalone SaaS admin portal served at /admin — not an Odoo app',
    'category': 'Hidden',
    'author': 'Zahed Hasan',
    'website': 'https://raptron.com',
    # website is included so our login/favicon overrides load AFTER website's templates
    'depends': ['base', 'mail', 'web', 'crm', 'account', 'website'],
    'data': [
        'security/raptron_admin_groups.xml',
        'security/ir.model.access.csv',
        'data/mail_templates.xml',
        'data/enforce_settings_cron.xml',
        'views/login_templates.xml',
        'views/web_layout.xml',
        'views/registration_views.xml',
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'assets': {
        'web.assets_backend': [
            'raptron_admin/static/src/css/cleanup.css',
        ],
        'web.assets_frontend': [
            'raptron_admin/static/src/css/login_style.css',
        ],
    },
    'license': 'LGPL-3',
}
