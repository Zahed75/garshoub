{
    'name': 'WhatsApp Integration',
    'version': '19.0.1.0.0',
    'summary': 'WhatsApp invoice sharing and automated payment reminders',
    'category': 'Accounting',
    'author': 'Al Garshoub',
    'website': 'https://garshoub.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/whatsapp_cron.xml',
        'views/account_move_views.xml',
        'views/whatsapp_message_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
