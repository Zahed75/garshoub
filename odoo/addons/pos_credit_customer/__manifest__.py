{
    'name': 'POS Credit Customer',
    'version': '19.0.1.0.0',
    'summary': 'POS Credit/Cash toggle + Customer Order History & Credit Limit',
    'category': 'Point of Sale',
    'author': 'Al Garshoub',
    'website': 'https://garshoub.com',
    'depends': ['point_of_sale', 'account'],
    'data': [
        'security/pos_credit_security.xml',
        'views/pos_order_views.xml',
        'views/res_partner_views.xml',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_credit_customer/static/src/js/pos_credit_button.js',
            'pos_credit_customer/static/src/js/pos_customer_info.js',
            'pos_credit_customer/static/src/xml/pos_credit_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
