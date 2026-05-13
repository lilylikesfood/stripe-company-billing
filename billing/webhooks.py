import stripe
import os

from flask import request
from dotenv import load_dotenv

from database.models import Contract, db

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

    except Exception as e:
        print(e)
        return str(e), 400
    
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

    if event['type'] == 'invoice.paid':
        invoice= event['data']['object']
        customer_id = invoice['customer']

        contract = Contract.query.filter_by(
            customer_id=customer_id
        ).first()

        if contract:

            contract.status = "active"

            db.session.commit()

            print("Contract marked active")
    
    if event['type'] == 'customer.subscription.deleted':
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
    if event['type'] == 'customer.subscription.updated':
        subscription= event['data']['object']
        subscription_id= subscription['id']

        contract= Contract.query.filter_by(
            subscription_id=subscription_id
        ).first()

        if contract:
            contract.subscription_status= subscription['status']

            db.session.commit()

            print("Subscription status updated")

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