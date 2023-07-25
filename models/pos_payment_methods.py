import json
import logging
import pprint
import random
import requests, hashlib, hmac
import string

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


'''
Part of the specifications require a separate
form for fixed configurations (like merchant hash key)
necessitating this model
'''
class IPayPosConfig(models.Model):
    _name = "ipay.pos.config"
    _description = "Configuration for ipay POS"

    #config details
    name = fields.Char(string="iPay Config Name", required=True, help="Config Name that the user gives")
    ipay_merchant_id = fields.Char(string="iPay Merchant Name", copy="False", help="The key given to your corporation by IPAY", default="demo")
    ipay_merchant_key = fields.Char(string="iPay Merchant Key", copy="False", help="The Hash Key given to your corporation by IPAY", default="demoCHANGED")
    ipay_sub_account = fields.Char(string="iPay Sub Account", help="The sub account given to you by iPay for mpesa/equitel transactions", default="77061")
    ipay_pos_live = fields.Boolean('live field', default=False, help="run pos payment in test mode")

    #fixed values
    ipay_pos_url = fields.Char('Hook URL', compute='_gen_endpoint', readonly=True, store=True)
    ipay_pos_hsh = fields.Char('Hash Key', compute='_gen_hash_key', readonly=True, store=True)
    
    #generate endpoints for ipays use
    @api.depends('ipay_merchant_id')
    def _gen_endpoint(self):
        #returns endpoint for the controller
        for ln in self:
            url_base = ''.join(self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
            ln.ipay_pos_url =  url_base + "/pos_ipay/collector"
            _logger.warning("URL set to %s", ln.ipay_pos_url)

    #generate single instance hashkey
    @api.depends('ipay_merchant_id')
    def _gen_hash_key(self):
        #returns hashkey for the endpoint
        for ln in self:
            letters = string.ascii_lowercase
            ln.ipay_pos_hsh = ''.join(random.choice(letters) for i in range(10))
            _logger.warning("Key set to %s", ln.ipay_pos_hsh)


    def _get_config(self):
        return {
            'ipay_merchant_id': self.ipay_merchant_id,
            'ipay_merchant_key': self.ipay_merchant_key,
            'ipay_pos_live': self.ipay_pos_live,
            'ipay_pos_url': self.ipay_pos_url,
            'ipay_pos_hsh': self.ipay_pos_hsh
        }

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('ipay', 'iPay')]

    ipay_pos_config_id = fields.Many2one('ipay.pos.config', string='iPay Credentials', help='The configuration of iPay used for this journal', store=True)

    #rpc caller notifications (it'll be polling this data). All tx specific
    consumed = fields.Boolean(string="consumed", help="technical field that tells the RPC caller that a new pos payment is consumable", default=False, copy=False)
    verified = fields.Boolean(string="verified", help="technical field that tells the RPC caller that the current consumable req had been verified", default=False, copy=False)
    amount = fields.Float(string="payed amount", copy=False)
    ipay_tx_id = fields.Char('Transaction ID', copy=False)

    #payment options
    ipay_card = fields.Boolean(string="Card Payments", help="Technical fields that tells the module what payment mode to expect", default=False) #0
    ipay_m_pesa = fields.Boolean(string="MPesa", help="Technical fields that tells the module what payment mode to expect", default=False) #1
    ipay_airtel_money = fields.Boolean(string="Airtel Money", help="Technical fields that tells the module what payment mode to expect", default=False) #0
    ipay_equitel = fields.Boolean(string="Equitel", help="Technical fields that tells the module what payment mode to expect", default=False) #1
    ipay_qr_code = fields.Boolean(string="QR Code", help="Technical fields that tells the module what payment mode to expect", default=False) #0

    def get_url(self):
        return  "https://payments.ipayafrica.com/v3/ke" 

    def check_ipay(self):
        self.ensure_one()
        r = requests.get(self.get_url())
        if r.status_code == 200:
            return True
        else:
            return False

    '''
    Whitelist fields so they can be written
    to by the controller
    '''
    def _is_write_forbidden(self, fields):
        whitelisted_fields = set(('consumed', 'verified', 'amount', 'ipay_tx_id'))
        return super(PosPaymentMethod, self)._is_write_forbidden(fields - whitelisted_fields)

    '''
    ensure_one to avoid concurrent update errors when
    polling ipays POS. Requires internet connection
    which isn't ensured by the POS (works offline).
    Polls both self for a consumable request(verified or not) 
    and IPAYs API for connectivity. 
    '''
    def poll_latest_ipay_request(self):
        self.ensure_one()

        # needs to post to ipay to ensure the 
        # connection is still live before waiting
        r = requests.get(self.get_url())
        gui_req = False
        channel = ""

        if self.ipay_equitel or self.ipay_m_pesa:
            gui_req = True
            if self.ipay_equitel:
                channel="eq"
            elif self.ipay_m_pesa:
                channel="mp"
            else:
                channel="default"
        if self.ipay_airtel_money or self.ipay_card or self.ipay_qr_code:
            gui_req = False

        if r.status_code == 200 and self.consumed:
            return {
                'up': True,
                'avail': True,
                'status': r.status_code,
                'message': r.reason,
                'verified': self.verified,
                'tx': self.ipay_tx_id,
                'amount': self.amount,
                'gui_req': gui_req,
                'chn': channel
            }
        elif r.status_code != 200 and self.consumed:
            return {
                'up': False,
                'avail': True,
                'status': r.status_code,
                'message': r.reason,
                'verified': self.verified,
                'tx': self.ipay_tx_id,
                'amount': self.amount,
                'gui_req': gui_req,
                'chn': channel
            }
        elif r.status_code == 200 and not self.consumed:
            return {
                'up': True,
                'avail': False,
                'status': r.status_code,
                'message': r.reason,
                'verified': self.verified,
                'tx': self.ipay_tx_id,
                'amount': self.amount,
                'gui_req': gui_req,
                'chn': channel
            }
        else:
            # connection down & no consumable
            return False

    '''
    Check the model above for why this is ensure_one.
    Closes consumed objects.
    '''
    def close(self):
        self.ensure_one()
        self.consumed = False
        self.verified = False
        self.amount = 0.0
        self.ipay_tx_id = ""

    def _get_url_act(self, chn):
        if chn == "eq":
            return "https://apis.ipayafrica.com/payments/v2/transact/manualpush/equitel"
        elif chn == "mp":
            return "https://apis.ipayafrica.com/payments/v2/transact/manualpush/mpesa"
        else:
            return ""

    '''
    Endpoint for STK pushes, calls the MPesa/
    Equitel stk api intergrators
    '''
    def pay_manual(self, number, amnt, curr):
        if self.ipay_equitel:
            channel = "eq"
        elif self.ipay_m_pesa:
            channel = "mp"
        else: 
            return False
        if curr is not 'KES':
            org = self.env['res.currency'].search([('name', '=', curr)])
            kes = self.env['res.currency'].search([('name', '=', 'KES')])
            amnt = org.compute(amnt, kes)
            _logger.info('currency converted:\n%s', pprint.pformat(amnt))
        data = {
            'phone': number,
            'vid': self.ipay_pos_config_id.ipay_merchant_id,
            'amount': amnt,
            'account': self.ipay_pos_config_id.ipay_sub_account
        }
        text_ = "{0}{1}{2}{3}".format( 
            data['phone'],
            data['vid'],
            data['amount'],
            data['account']
        )
        hashobj = hmac.new(self.ipay_pos_config_id.ipay_merchant_key.encode(), text_.encode(), hashlib.sha256)
        hashtxt = hashobj.hexdigest()
        data['hash'] = hashtxt
        _logger.info('Payment request sent out for number:%s\n', pprint.pformat(data['phone']))
        return requests.post(self._get_url_act(channel), data=data).json()

    '''
    Any transactions with negative values are 
    assumed to be refunds, processed differently
    '''
    def refund_tx(self, id):
        url = "https://apis.ipayafrica.com/payments/v2/transaction/refund"
        vid = self.ipay_pos_config_id.ipay_merchant_id
        txt = "code={0}&vid={1}".format(id, vid)
        hashobj = hmac.new(self.ipay_pos_config_id.ipay_merchant_key.encode(), txt.encode(), hashlib.sha256)
        hsh = hashobj.hexdigest()
        dt = {
            "code": id,
            "vid": vid,
            "hash": hsh
        }
        _logger.info('refund request sent out for transaction:%s\n', pprint.pformat(dt['code']))
        return requests.post(url, data=dt).json()

'''
This model is necessary to ensure duplicates arent processed.
Maintaining certain user information is necessary for this,
the most efficient way to maintain & search user information
is thorugh a relation
'''
class IPayPosPayments(models.Model):
    _name = "ipay.pos.order"
    _description = "Point of Sale Orders processed by IPay"

    #user info
    name = fields.Char(string="user name", help="user name")
    number = fields.Char(string="user number", help="user number")
    channel = fields.Char(string="payment channel")
    amount = fields.Char(string="payment amount")
    t_stamp = fields.Date(string="payment time")
