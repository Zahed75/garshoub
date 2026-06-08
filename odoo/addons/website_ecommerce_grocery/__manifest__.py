{
    'name': 'Website Ecommerce Grocery',
    'version': '19.0.1.0.0',
    'summary': 'Ecommerce catalog + Telr payment gateway for Al Garshoub',
    'category': 'Website',
    'author': 'Al Garshoub',
    'website': 'https://garshoub.com',
    'depends': ['website', 'website_sale', 'payment'],
    'data': [
        'views/website_templates.xml',
        'views/product_category_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_ecommerce_grocery/static/src/css/grocery_theme.css',
            'website_ecommerce_grocery/static/src/js/grocery_filters.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
