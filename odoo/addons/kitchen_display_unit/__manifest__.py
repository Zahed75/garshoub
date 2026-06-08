{
    'name': 'Kitchen Display Unit',
    'version': '19.0.1.0.0',
    'summary': 'Real-time kitchen display for delivery orders',
    'category': 'Point of Sale',
    'author': 'Al Garshoub',
    'website': 'https://garshoub.com',
    'depends': ['point_of_sale', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/kitchen_order_views.xml',
        'views/kitchen_display_templates.xml',
        'views/pos_config_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
