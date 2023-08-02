# Part of Odoo. See LICENSE file for full copyright and licensing details.

from hashlib import sha1

from werkzeug import urls

from odoo import fields, models

class iPayPaymentProvider(models.Model):
    _description = "iPay Payment Provider"
    _inherit = ['ipay.pos.config']


class InheritPaymentProvider(models.Model):
    _inherit = 'payment.provider'
    _description = 'Payment Provider Inherited'