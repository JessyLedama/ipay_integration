# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Provider: iPay',
    'version': '2.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A Online payment provider covering several countries in Africa.",
    'depends': ['payment', 'ipay_integration'],
    'data': [
        'views/payment_ipay_templates.xml',
        'views/payment_provider_views.xml',

        'data/payment_provider_data.xml',
    ],
    'application': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
