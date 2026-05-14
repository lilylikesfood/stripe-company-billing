import stripe
import os

from flask import request
from dotenv import load_dotenv

from database.models import Contract, db, WebhookEvent

from datetime import datetime, timezone

load_dotenv()

endpoint_secret= os.getenv("STRIPE_WEBHOOK_SECRET")

def handle_webhook():

    payload= request.data

    sig_header= request.headers.get('Stripe-Signature')

    try: 
        event= stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )

        # Prevent Stripe from processing the SAME webhook twice
        stripe_event_id= event['id']

        existing_event= WebhookEvent.query.filter_by(
            stripe_event_id= stripe_event_id
        ).first()

        if existing_event:
            print("Webhook already processed. :D")

            return '', 200
        
        webhook_event= WebhookEvent(
            stripe_event_id= stripe_event_id,
            event_type=event['type']
        )

        db.session.add(webhook_event)
        db.session.commit()

    except Exception as e:
        print(e)
        return str(e), 400
    
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
            db.session.commit()
            print("Contract marked overdue")

    elif event['type'] == 'invoice.paid':
        invoice= event['data']['object']
        customer_id = invoice['customer']

        contract = Contract.query.filter_by(
            customer_id=customer_id
        ).first()

        if contract:

            contract.status = "active"

            db.session.commit()

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

            db.session.commit()

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

            db.session.commit()

            print("Subscription status updated")

    webhook_event.processed= True
    webhook_event.processed_at= datetime.now(timezone.utc)

    db.session.commit()

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