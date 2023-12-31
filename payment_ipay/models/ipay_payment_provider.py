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
    code = fields.Selection(
        selection_add=[('ipay', "iPay")], ondelete={'ipay': 'set default'})
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
    show_allow_tokenization = fields.Boolean(string='Show Allow Tokenization Supported', default=True)
    show_payment_icon_ids = fields.Boolean(string='Show Payment Icon', default=True)
    show_pre_msg = fields.Boolean(string='Show Pre Message', default=True)
    show_pending_msg = fields.Boolean(string='Show Pending Message', default=True)
    show_auth_msg = fields.Boolean(string='Show Auth Message', default=True)
    show_cancel_msg = fields.Boolean(string='Show Cancel Message', default=True)
    so_reference_type = fields.Selection([('so_name', 'Based on document reference'), ('partner', 'Based on Partner ID')], string='Communication')
    show_pre_msg = fields.Boolean(string='Show Pre Message', default=True)
    show_done_msg = fields.Boolean(string='Show Done Message', default=True)
    support_refund = fields.Selection([('full_only', 'Full Only'), ('partial', 'Partial')], string='Type of Refund Supported')
    write_date = fields.Datetime(string='Last Updated On')
    create_date = fields.Datetime(string='Created On')
    write_uid = fields.Many2one('res.users', string="Last Updated By")
    code = fields.Selection([('none', 'No Provider Set'), ('demo', 'Demo'), ('ipay', 'iPay')], string="Code", help="The technical code of this payment provider")
    image_128 = fields.Binary(string="Image")
    state = fields.Selection([('disabled', 'Disabled'), ('enabled', 'Enabled'), ('test', 'Test')])
    display_as = fields.Char(string="Displayed As", help="Description of the provider for customers")
    payment_icon_ids = fields.Many2many('payment.icon',string="Supported Payment Icons")
    allow_tokenization = fields.Boolean(string="Allow Saving Payment Methods", default=True)
    capture_manually = fields.Boolean(string="Capture Amount Manually")
    allow_express_checkout = fields.Boolean(string='Allow Express Checkout Supported')
    maximum_amount = fields.Monetary(string='Maximum Amount', currency_field="main_currency_id", help="The maximum payment amount that this payment provider is available for. Leave blank to make it available for any payment amount.")
    available_country_ids = fields.Many2many('res.country', string="Countries")
    auth_msg = fields.Html(string="Authorize Message")
    cancel_msg = fields.Html(string="Canceled Message")
    journal_id = fields.Many2one('account.journal', string="Payment Journal")
    sequence = fields.Integer(string='Sequence')
    __last_update = fields.Datetime(string="Last Modified On")
    create_uid = fields.Many2one('res.users', string="Created By")
    done_msg = fields.Html(string="Done Message")
    fees_active = fields.Boolean(string="Add Extra Fees")
    express_checkout_form_view_id = fields.Many2one('ir.ui.view', string="Express Checkout Form Template")
    display_name = fields.Char(string="Display Name")
    fees_dom_fixed = fields.Float(string="Fixed Domestic Fees")
    fees_dom_var = fields.Float(string="Variable Domestic Fees (%)")
    fees_int_fixed = fields.Float(string="Fixed International Fees")
    # id = fields.Integer(string="ID")
    inline_form_view_id = fields.Many2one('ir.ui.view', string="Inline Form Template")
    redirect_form_view_id = fields.Many2one('ir.ui.view', string="Redirect From Template", help="The template rendering a form submitted to redirect the user when making a payment")
    token_inline_form_view_id = fields.Many2one('ir.ui.view', string="Token Inline Form Template")
    fees_int_var = fields.Float(string="Variable International Fees (%)")
    pre_msg = fields.Html(string="Help Message")
    
    





    #fixed values
    ipay_pos_url = fields.Char('Hook URL', compute='_gen_endpoint', readonly=True, store=True)
    ipay_pos_hsh = fields.Char('Hash Key', compute='_gen_hash_key', readonly=True, store=True)