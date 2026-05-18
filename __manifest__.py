{
    'name': 'Pharmacy Management',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Handle all pharmacy management operations.',
    'author': 'Azhar Ali',
    'depends': [
        'base',
        'base_setup',
        'web',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'data/pharmacy_dashboard_data.xml',

        'views/category_views.xml',
        'views/medicine_views.xml',
        'views/supplier_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'views/expense_views.xml',
        'views/dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',

        'reports/pharmacy_sale_receipt_report.xml',
        'reports/pharmacy_period_sales_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pharmacy_management_system/static/src/css/pharmacy_management.css',
            'pharmacy_management_system/static/src/lib/chart/chart.min.js',
            'pharmacy_management_system/static/src/js/pharmacy_orders.js',
            'pharmacy_management_system/static/src/js/pharmacy_dashboard.js',
            'pharmacy_management_system/static/src/xml/pharmacy_orders.xml',
            'pharmacy_management_system/static/src/xml/pharmacy_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}