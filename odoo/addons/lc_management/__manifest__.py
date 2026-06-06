{
    'name': 'Bangladesh LC Management',
    'version': '19.0.1.0.0',
    'summary': 'Full Import/Export Letter of Credit lifecycle — Bangladesh trade finance (BB regulations)',
    'description': """
Bangladesh Letter of Credit (LC) Management
============================================

A comprehensive Odoo module for managing the full LC lifecycle as per
Bangladesh Bank (BB) foreign exchange regulations.

Features
--------
* Import LC & Export LC — both covered
* 6-state lifecycle: Draft → Applied → Opened → Docs Received → Retired → Closed
* Automatic margin journal entries (BB-mandated margin %)
* EXP Form gate — blocks export delivery if EXP number missing
* LCA Form gate — required for Import LC application
* IRC/ERC certificate expiry warnings (30-day advance cron)
* NBR customs duty routing — auto-creates partner for National Board of Revenue
* Landed cost integration for import duty distribution
* Linked to Purchase Orders, Sale Orders, and Account Journal Entries
    """,
    'category': 'Accounting/Finance',
    'author': 'Zahed Hasan',
    'website': 'https://raptron.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'purchase',
        'sale_management',
        'stock',
        'stock_landed_costs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/lc_demo_data.xml',
        'views/letter_of_credit_views.xml',
        'views/lc_menu.xml',
        'views/res_partner_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
