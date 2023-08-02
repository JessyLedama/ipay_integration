# Part of Odoo. See LICENSE file for full copyright and licensing details.

from hashlib import sha1

from werkzeug import urls

from odoo import fields, models

class iPayPaymentProvider(models.Model):
    _name = 'ipay.payment.provider'
    _description = "iPay Payment Provider"
    _inherit = ['ipay.pos.config', 'payment.provider']

    
    
    #config details
    name = fields.Char(string="iPay Config Name", required=True, help="Config Name that the user gives")
    ipay_merchant_id = fields.Char(string="iPay Merchant Name", copy="False", help="The key given to your corporation by IPAY", default="demo")
    ipay_merchant_key = fields.Char(string="iPay Merchant Key", copy="False", help="The Hash Key given to your corporation by IPAY", default="demoCHANGED")
    ipay_sub_account = fields.Char(string="iPay Sub Account", help="The sub account given to you by iPay for mpesa/equitel transactions", default="77061")
    ipay_pos_live = fields.Boolean('live field', default=False, help="run pos payment in test mode")
    # company_id = fields.Many2one('res.company', string="Company")
    # website_id = fields.Many2one('website', string="Website")
    # is_published = fields.Boolean(string='Published', default=False)
    # main_currency_id = fields.Many2one('res.currency', string="Currency")
    available_countries_ids = fields.Many2many('res.country', string="Country")

    #fixed values
    ipay_pos_url = fields.Char('Hook URL', compute='_gen_endpoint', readonly=True, store=True)
    ipay_pos_hsh = fields.Char('Hash Key', compute='_gen_hash_key', readonly=True, store=True)