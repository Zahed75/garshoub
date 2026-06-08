{
    'name': 'Inventory Source Tracking',
    'version': '19.0.1.0.0',
    'summary': 'Add "Source from Others" field on stock pickings',
    'category': 'Inventory',
    'author': 'Al Garshoub',
    'website': 'https://garshoub.com',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_views.xml',
        'reports/stock_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
