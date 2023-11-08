# Payments

Payments work with stripe. 

Reference link: https://stripe.com/docs/webhooks/quickstart

For a developer to forward a stripe webhook to a development website, run:

```
stripe listen --forward-to localhost:3000/webhook
```

Docs for simulating payments: https://stripe.com/docs/testing

Docs for installing stripe cli: https://stripe.com/docs/stripe-cli

Webhook signature secret comes from the "stripe listen" command.


Redirect customer Doc - https://stripe.com/docs/js/deprecated/redirect_to_checkout (Deprecated)

Current redirect docs - https://stripe.com/docs/payments/checkout/how-checkout-works
