-- disable ipay payment provider
UPDATE payment_provider
   SET ipay_mechant_id = NULL;
       ipay_merchant_key = NULL,
       ipay_sub_account = NULL;
