odoo.define('pos_ipay.models', function(require){
    var models = require('point_of_sale.models');
    var PaymentIpay = require('pos_ipay.payment');

    models.register_payment_method('ipay', PaymentIpay);
    models.load_fields('pos.payment.method', ['ipay_pos_config_id']);
});