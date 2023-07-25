odoo.define('pos_ipay.payment', function (require) {
    "use strict";
    
    var core = require('web.core');
    var rpc = require('web.rpc');
    var PaymentInterface = require('point_of_sale.PaymentInterface');
    const { Gui } = require('point_of_sale.Gui');
    
    var _t = core._t;
    
    var PaymentIpay = PaymentInterface.extend({
        send_payment_request: function (cid) {
            this._super.apply(this, arguments);
            this._reset_state();
            this.was_cancelled = false;
            return this._ipay_pay();
        },

        send_payment_cancel: function (order, cid) {
            this._super.apply(this, arguments);
            // set only if we are polling
            this.was_cancelled = !!this.polling;
            globalThis.cancelled = true;
            console.log(cid);
            return this.was_cancelled;
        },

        close: function () {
            this._super.apply(this, arguments);
        },

        _reset_state: function () {
            this.was_cancelled = false;
            this.last_diagnosis_service_id = false;
            this.remaining_polls = 2;
            this.resolved = false;
            clearTimeout(this.polling);
        },
    
        _handle_odoo_connection_failure: function (data) {
            var line = this.pos.get_order().selected_paymentline;
            if (line) {
                line.set_payment_status('retry');
            }
            this._show_error(_('Connection reset, please try again.'));
            return Promise.reject(data); // prevent subsequent onFullFilled's from being called
        },
    
        _call_ipay: function () {
            var self = this;
            return rpc.query({
                model: 'pos.payment.method',
                method: 'poll_latest_ipay_request',
                args: [[this.payment_method.id]]
            }, {
                // polls for a live internet connection and available request
                timeout: 5000,
                shadow: true,
            }).catch(this._handle_odoo_connection_failure.bind(this));
        },
        
        _convert_receipt_info: function (id) {
            console.log(typeof(id));
            return '<br/>iPay Transaction ID : ' + id + '<br/>';
        },

        _ipay_pay: function () {
            var self = this;

            return this._call_ipay().then(function (data) {
                return self._ipay_handle_response(data);
            });
        },
        
        _ipay_close: function () {
            var self = this;
            return rpc.query({
                model: 'pos.payment.method',
                method: 'close',
                args: [[this.payment_method.id]]
            }, {
                // closes the current consumable request
                timeout: 10000,
                shadow: true,
            }).catch(this._handle_odoo_connection_failure.bind(this));
        },
    
        _poll_for_response: function (resolve, reject) {
            var self = this;
            if (this.was_cancelled) {
                return Promise.resolve();
            }

            if (this.resolved) {
                return Promise.resolve();
            }
    
            return rpc.query({
                model: 'pos.payment.method',
                method: 'poll_latest_ipay_request',
                args: [[this.payment_method.id]]
            }, {
                timeout: 5000,
                shadow: true,
            }).catch(function (data) {
                reject();
                return self._handle_odoo_connection_failure(data);
            }).then(function (status) {
                var order = self.pos.get_order();
                var line = order.selected_paymentline;

                if(self.was_cancelled){
                    resolve(false);
                }

                if (status.up){
                    if(status.avail){
                        if (status.verified){                       
                            if(response.amount < line.amount){
                                line.amount -= response.amount;
                                if (line.amount <= 0){
                                    line.set_payment_status('done');
                                    line.ipay_data = true;
                                    line.ipay_tx = status.tx;
                                    line.transaction_id = status.tx;
                                    line.set_receipt_info(self._convert_receipt_info(status.tx));
                                    resolve(true);
                                }
                                resolve(true);
                            } else {
                                line.set_payment_status('done');
                                line.ipay_data = true;
                                line.ipay_tx = status.tx;
                                line.transaction_id = status.tx;
                                line.set_receipt_info(self._convert_receipt_info(status.tx));
                                resolve(true);
                            }
                        }
                        else{
                            var message = "Couldn't verify the payment, check if the Merchant Information configured is correct";
                            self._show_error(_.str.sprintf(_t('%s'), message));
                            line.set_payment_status('retry');
                            reject();
                        }
                    } else {
                        self.remaining_polls--;
                        if(self.remaining_polls < -15){
                            self._show_error(_t('The connection timed out. Please try paying again'));
                            line.set_payment_status('retry');
                            resolve(false);
                        }
                    }
                } else {
                    self.remaining_polls--;
                    console.log(self.remaining_polls);
                    if(self.remaining_polls <= 0){
                        self._show_error(_t('The connection was reset, please check that you are connected and retry.'));
                        line.set_payment_status('retry');
                        self._ipay_close();
                        resolve(false);
                    }
                }
            });
        },
    
        _ipay_handle_response: async function (response) {
            var self = this;
            var line = this.pos.get_order().selected_paymentline;

            // Tx is a refund
            if(line.amount<0){
                if(globalThis.tid == null || globalThis.tid == ""){
                    console.log("refund");
                    const {confirmed, payload} = await Gui.showPopup('TextAreaPopup', {
                        title: 'Add Transaction ID from the receipt',
                        startingValue: '',
                    });
                    if(confirmed){
                        globalThis.tid = payload; 
                        r = rpc.query({
                            model: 'pos.payment.method',
                            method: 'refund_tx',
                            args: [[this.payment_method.id], globalThis.tid]
                        }, {
                            timeout: 5000,
                            shadow: true,
                        }).catch (function(data){ 
                            self._handle_odoo_connection_failure(data);
                        });
                        r.then(function(r){
                            console.log(r);
                            if(r.status == 200 && r.text == "Refund done"){
                                console.log("refund done");
                                line.ipay_data = true;
                                line.ipay_tx = response.tx;
                                globalThis.tid = "";
                                line.set_payment_status('done');
                                line.set_receipt_info(self._convert_receipt_info(response.tx))
                                self.resolved = true;
                                return Promise.resolve(true);
                            }else {
                                self._show_error("Refund Failed. Check your config and the transaction ID and try again.");
                                line.set_payment_status('retry');
                                globalThis.tid = "";
                                return Promise.resolve(false);
                            }    
                        });
                    } else {
                            globalThis.tid = "";
                            this._show_error("Refund Failed. Enter the Transaction ID from the receipt before refunding.");
                            return Promise.resolve(false);
                    }
                }
            }

            if (!response) {
                this._show_error(_t('Connection failed. Odoo needs an active connection to pay via IPAY'));
                return Promise.resolve();
            }

            if (response.up && !response.avail) {
                this.phn = 0;
                if (globalThis.phn > 0){
                    if(/^(07)([0-9]{8})$/.test(globalThis.phn)){
                        globalThis.phn = "" + globalThis.phn;
                    } else if(/^(254)([0-9]{8})$/.test(globalThis.phn)){
                        globalThis.phn = "" + globalThis.phn;
                    } else if(/^(7)([0-9]{8})$/.test(globalThis.phn)){
                        globalThis.phn = "0" + globalThis.phn;
                    } else {
                        self._show_error("The phone number entered was Invalid");
                        line.set_payment_status('force_done');
                        return Promise.resolve(false);
                    }
                }

                var r;
                // Manual push using rpc call before entering
                // async wait for model values to change
                if(response.chn == "eq" || response.chn == "mp"){
                    if(line.amount > 0){
                        const { confirmed, payload } = await Gui.showPopup('NumberPopup', {
                            title: 'Add Phone Number',
                            startingValue: 0,
                        });
                        if (confirmed) {
                            globalThis.phn = payload;
                            console.log(this.pos.currency.name);
                            r = rpc.query({
                                model: 'pos.payment.method',
                                method: 'pay_manual',
                                args: [[this.payment_method.id], globalThis.phn, 1.0, "KES"]
                            }, {
                                timeout: 5000,
                                shadow: true,
                            }).catch (function(data){ 
                                self._handle_odoo_connection_failure(data);
                            });
                            r.then(function(r){
                                console.log(r);
                                if(!r){
                                    globalThis.phn = 0;
                                    self._show_error("Please configure either equitel or mpesa to use STK pushes");
                                    return Promise.resolve(false);
                                }
                                if(r.status != 1) {
                                    globalThis.phn = 0;
                                    console.log(r.status);
                                    self._show_error("Please confirm the phone number and iPay configurations are correct ");
                                    return Promise.resolve(false);
                                } else {console.log(r.status);}
                            });
                        } else {
                            this._show_error("This payment method requires the users phone number to process payments");
                            return Promise.resolve(false);
                        }
                    }
                }

                line.set_payment_status('waiting');
                var self = this;
                var res = new Promise(function(resolve, reject){
                    clearTimeout(self.polling);
                    self.polling = setInterval(function (){
                        self._poll_for_response(resolve, reject);
                    }, 4000);
                });
                
                res.finally(function(){
                    self._reset_state();
                    self._ipay_close();
                });

                return res;
            } else if(response.up && response.verified){
                if(response.amount < line.amount){
                    line.amount -= response.amount;
                    if(line.amount<=0){
                        self._reset_state();
                        self._ipay_close();
                        line.ipay_data = true;
                        line.ipay_tx = response.tx;
                        line.transaction_id = response.tx;
                        line.set_receipt_info(self._convert_receipt_info(response.tx));
                        return Promise.resolve(true);
                    }
                    return Promise.resolve(true);
                } else {
                    self._reset_state();
                    self._ipay_close();
                    line.ipay_data = true;
                    line.ipay_tx = response.tx;
                    line.transaction_id = response.tx;
                    line.set_receipt_info(self._convert_receipt_info(response.tx));
                    return Promise.resolve(true);
                }
            }
        },
    
        _show_error: function (msg, title) {
            if (!title) {
                title =  _t('Ipay Error');
            }
            Gui.showPopup('ErrorPopup',{
                'title': title,
                'body': msg,
            });
        },
    });

    return PaymentIpay;
    });
    