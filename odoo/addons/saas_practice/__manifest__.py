{
    'name': 'SaaS Practice Module',
    'version': '1.0',
    'summary': 'Practice module for SaaS database creation via /admin portal',
    'category': 'Tools',
    'author': 'Zahed',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_server.xml',
        'views/saas_client_views.xml',
        'views/admin_template.xml',
        'views/hide_expiration.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'saas_practice/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
