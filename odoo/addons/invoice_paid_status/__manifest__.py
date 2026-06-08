{
    'name': 'Invoice Paid Status',
    'version': '19.0.1.0.0',
    'summary': 'Add Paid/Partial/Unpaid status column on invoice tree view',
    'category': 'Accounting',
    'author': 'Al Garshoub',
    'website': 'https://garshoub.com',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
