import stripe
import os

from flask import request
from dotenv import load_dotenv

from database.models import Contract, db, WebhookEvent

from datetime import datetime, timezone

load_dotenv()

endpoint_secret= os.getenv("STRIPE_WEBHOOK_SECRET")

# Separate Business Logic From HTTP Route
def process_webhook_event(event, webhook_event):
    """
    Apply Stripe webhook business logic
    and update webhook processing state.
    """
    # Business logic starts
    # webhook logging mindset (helps debugging)
    print("Webhook event:", event['type'])

    if event['type'] == 'invoice.payment_failed':
        invoice= event['data']['object']
        customer_id= invoice['customer']
        
        # debugging
        print("Webhook customer:", customer_id)

        contract= Contract.query.filter_by(
            customer_id= customer_id
        ).first()

        # debugging
        print("Found contract:", contract)

        if contract:
            contract.status= "overdue"
            print("Contract marked overdue")

    elif event['type'] == 'invoice.paid':
        invoice= event['data']['object']
        customer_id = invoice['customer']

        contract = Contract.query.filter_by(
            customer_id=customer_id
        ).first()

        if contract:

            contract.status = "active"

            print("Contract marked active")
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription= event['data']['object']
        subscription_id= subscription['id']

        contract= Contract.query.filter_by(
            # Why subscription_id better than customer_id:
            # one customer can have multiple subscriptions
            subscription_id= subscription_id
        ).first()

        if contract:
            contract.status= "canceled"

            print("Contract canceled")

    # Subscription Status Tracking
    elif event['type'] == 'customer.subscription.updated':
        subscription= event['data']['object']
        subscription_id= subscription['id']

        contract= Contract.query.filter_by(
            subscription_id=subscription_id
        ).first()

        if contract:
            contract.subscription_status= subscription['status']

            print("Subscription status updated")

    webhook_event.processed= True
    webhook_event.processed_at= datetime.now(timezone.utc)


def handle_webhook():

    raw_payload= request.data

    sig_header= request.headers.get('Stripe-Signature')

    # try/except is mainly protecting construct_event for invalid signature, malformed payload, Stripe verification failure
    try: 
        event= stripe.Webhook.construct_event(
            raw_payload,
            sig_header,
            endpoint_secret
        )
        # webhook verification should not be put in transaction bcz 
        # it’s external verification logic
        # not database state
        # Transactions should usually protect:
        # database consistency
        # not external API parsing

        # Prevent Stripe from processing the SAME webhook twice
        stripe_event_id= event['id']

        existing_event= WebhookEvent.query.filter_by(
            stripe_event_id= stripe_event_id
        ).first()

        # should stay outside transaction bcz it’s just a quick read/check
        # we want fast early exit
        # no reason to open transaction if already completed
        if existing_event and existing_event.processed:
            print("Webhook already fully processed. :D")

            return '', 200
    except Exception as e:
        print(e)
        return str(e), 400
    
    # Persist Event First
    # prevent database crash when Stripe retries use the SAME event ID
    # if not thing:
    # usually means: "If thing does not exist"
    if not existing_event:
        webhook_event= WebhookEvent(
            stripe_event_id= stripe_event_id,
            event_type=event['type'],
            # serialization
            # Convert Stripe custom object into normal Python dictionary
            payload=event.to_dict()
        )
        # it return None or actual object, not false or true

        db.session.add(webhook_event)
        db.session.commit()
    
    else:
        webhook_event= existing_event
        
    # Database transactions- A transaction groups multiple database changes into one all-or-nothing operation.
    # Either EVERYTHING succeeds OR NOTHING succeeds 
    # Transaction Should Protect EVERYTHING Database-Related
    with db.session.begin():
    # meaning: "Start protected transaction block."
    # automatically commits if successful Or rolls back if crash happens

        process_webhook_event(event, webhook_event)

    return '', 200

# system definition
# Status	        Meaning
# -----------------------------------------------
# active	        subscription healthy
# overdue	        payment failed
# canceled	        subscription canceled
# expired	        contract fully ended
# inspection_due	inspection period ended
# suspended	        temporarily disabled
# pending	        awaiting first payment

# '' & "" Both are strings

# CASE 1 — Brand New Webhook
# Database finds NOTHING.
# So:
# existing_event = None
# Then:
# not existing_event
# becomes:
# not None
# Python evaluates that as:
# True
# So:
# if not existing_event:
# DOES execute.

# Value	    Truthy/Falsy
# -----------------------
# None	    False
# actual    object	True