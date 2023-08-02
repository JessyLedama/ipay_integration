# Part of Odoo. See LICENSE file for full copyright and licensing details.

from hashlib import sha1

from werkzeug import urls

from odoo import fields, models

class iPayPaymentProvider(models.Model):
    _description = "iPay Payment Provider"
    _inherit = 'ipay.pos.config'

    
    
    #config details
    name = fields.Char(string="iPay Config Name", required=True, help="Config Name that the user gives")
    ipay_merchant_id = fields.Char(string="iPay Merchant Name", copy="False", help="The key given to your corporation by IPAY", default="demo")
    ipay_merchant_key = fields.Char(string="iPay Merchant Key", copy="False", help="The Hash Key given to your corporation by IPAY", default="demoCHANGED")
    ipay_sub_account = fields.Char(string="iPay Sub Account", help="The sub account given to you by iPay for mpesa/equitel transactions", default="77061")
    ipay_pos_live = fields.Boolean('live field', default=False, help="run pos payment in test mode")

    # payment provider details
    company_id = fields.Many2one('res.company', string="Company")
    website_id = fields.Many2one('website', string="Website")
    is_published = fields.Boolean(string='Published', default=False)
    main_currency_id = fields.Many2one('res.currency', string="Currency")
    support_fees = fields.Boolean(string='Fees Supported', default=True)
    support_manual_capture = fields.Boolean(string='Manual Capture Supported', default=True)
    support_tokenization = fields.Boolean(string='Tokenization Supported', default=True)
    support_express_checkout = fields.Boolean(string='Express Checkout Supported', default=True)
    module_id = fields.Many2one('ir.module.module', string='Corresponding Module')
    module_state = fields.Selection([('uninstalled', 'Uninstalled'), ('installed', 'Installed')], string="Installation State", default='uninstalled')
    module_to_buy = fields.Boolean(string="Odoo Enterprise Module", default=False)
    show_credentials_page = fields.Boolean(string='Show Credentials Page', default=True)
    show_allow_express_checkout = fields.Boolean(string='Show Allow Express Checkout Supported', default=True)
    

    #fixed values
    ipay_pos_url = fields.Char('Hook URL', compute='_gen_endpoint', readonly=True, store=True)
    ipay_pos_hsh = fields.Char('Hash Key', compute='_gen_hash_key', readonly=True, store=True)