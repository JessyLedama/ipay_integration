# Part of Odoo. See LICENSE file for full copyright and licensing details.

from hashlib import sha1

from werkzeug import urls

from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'
 
    code = fields.Selection(
        selection_add=[('ipay', "iPay")], ondelete={'ipay': 'set default'})
    ipay_merchant_id = fields.Char(
        string="iPay Merchant Name", help="The key given to your company by iPay", required_if_provider='ipay')
    ipay_merchant_key = fields.Char(
        string="iPay Merchant Key", help="The HASH key sgiven to your company by iPay", required_if_provider='ipay')
    ipay_sub_account = fields.Char(
        string="iPay Sub Account", help="The sub account givent to you by iPay for mpesa/equitel transactions", required_if_provider='ipay', groups='base.group_system')

    def _ipay_get_api_url(self):
        """ Return the API URL according to the state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://checkout.ipay.com/html/'
        else:
            return 'https://testcheckout.ipay.com/html/'

    def _ipay_generate_digital_sign(self, values, incoming=True):
        """ Generate the shasign for incoming or outgoing communications.

        :param dict values: The values used to generate the signature
        :param bool incoming: Whether the signature must be generated for an incoming (iPay to
                              Odoo) or outgoing (Odoo to iPay) communication.
        :return: The shasign
        :rtype: str
        """
        if incoming:
            # Incoming communication values must be URL-decoded before checking the signature. The
            # key 'brq_signature' must be ignored.
            items = [
                (k, urls.url_unquote_plus(v)) for k, v in values.items()
                if k.lower() != 'brq_signature'
            ]
        else:
            items = values.items()
        # Only use items whose key starts with 'add_', 'brq_', or 'cust_' (case insensitive)
        filtered_items = [
            (k, v) for k, v in items
            if any(k.lower().startswith(key_prefix) for key_prefix in ('add_', 'brq_', 'cust_'))
        ]
        # Sort parameters by lower-cased key. Not upper-case because ord('A') < ord('_') < ord('a').
        sorted_items = sorted(filtered_items, key=lambda pair: pair[0].lower())
        # Build the signing string by concatenating all parameters
        sign_string = ''.join(f'{k}={v or ""}' for k, v in sorted_items)
        # Append the pre-shared secret key to the signing string
        sign_string += self.ipay_merchant_key
        # Calculate the SHA-1 hash over the signing string
        return sha1(sign_string.encode('utf-8')).hexdigest()
