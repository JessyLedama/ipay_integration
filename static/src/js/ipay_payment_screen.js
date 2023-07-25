odoo.define('pos_ipay.iPayPaymentScreen', function (require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');

    const IPayPaymentScreen = PaymentScreen => 
        class extends PaymentScreen{
            constructor (){
                super(...arguments);
                this.phNumber = 0;
            }
            async addNumber(){
                //user click on Number POS screen
                globalThis.phn = 0;
                const { confirmed, payload } = await this.showPopup('NumberPopup', {
                    title: this.env._t('Add Phone Number'),
                    startingValue: 0,
                });
                if (confirmed) {
                    this.phNumber = parseInt(payload);
                    globalThis.phn = this.phNumber;
                }
            }
            async addID(){
                globalThis.tid = "";
                const {confirmed, payload} = await this.showPopup('TextAreaPopup', {
                    title: this.env._t('Add Transaction ID'),
                    startingValue: '',
                });
                if (confirmed) {
                    globalThis.tid = payload;
                }
            }
        };

    IPayPaymentScreen.template = 'pos_ipay.PaymentScreen';
    Registries.Component.extend(PaymentScreen, IPayPaymentScreen);
    return IPayPaymentScreen; 
});