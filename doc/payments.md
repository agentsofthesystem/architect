# Payments

Payments work with stripe.

Reference link: https://stripe.com/docs/webhooks/quickstart

## Development / Testing using listener tool.

For a developer to forward a stripe webhook to a development website, run:

```
stripe listen --forward-to localhost:3000/webhook
```

Docs for simulating payments: https://stripe.com/docs/testing

Docs for installing stripe cli: https://stripe.com/docs/stripe-cli

Webhook signature secret comes from the "stripe listen" command.


Redirect customer Doc - https://stripe.com/docs/js/deprecated/redirect_to_checkout (Deprecated)

Current redirect docs - https://stripe.com/docs/payments/checkout/how-checkout-works


## Setting up webhooks without listener for production

1. Make sure https://<domain>.com/webhook is available and publicly accessible.
2. Go https://dashboard.stripe.com/test/webhooks
3. Enter a the publically sucessful URL and select the event types that the webhook may receive.
   That info is on [here](../application/api/public/views.py).  See the webhook endpoint.
4. After creating the secret. Obtain the webhook signing secret.  You do not need the webhook ID.
5. As admin, enable payments and populate STRIPE_* settings.

Have a look here for more info: https://docs.stripe.com/webhooks

NOTE:
* If you add more event types then you have to go add it on the webhook page.
* It's possible to do all the setup for a webhook programmatically in code, but more management to
  do manually.

## Stripe settings

* STRIPE_PUBLISHABLE_KEY - Overal API Public Key of format "pk_abc123"
* STRIPE_SECRET_KEY - Overall API secret of format "sk_abc123"
* STRIPE_PRICE_ID_1 - Monthly Subscription Price ID - May others later.
* STRIPE_WEBHOOK_SECRET - This comes from the webhook page.