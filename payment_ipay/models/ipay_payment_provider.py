# Part of Odoo. See LICENSE file for full copyright and licensing details.

from hashlib import sha1

from werkzeug import urls

from odoo import fields, models

class iPayPaymentProvider(models.Model):
    _name = 'ipay.payment.provider'
    _description = "iPay Payment Provider"
    _inherit = ['ipay.pos.config', 'payment.provider']