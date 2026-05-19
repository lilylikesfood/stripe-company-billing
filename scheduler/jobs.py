from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta

from database.models import Contract,db

import stripe
# from flask import current_app
# error: circular import
# from app import app

from billing.webhooks import process_webhook_event
from database.models import WebhookEvent

# This file handles: scheduled business automation
# annual increases
# removing inspection fee
# late fee automation
# overdue balances
# reminders

def run_annual_increase():
    today= datetime.now()

    print("Running annual increase job: ",today)

# automation
def inspection_reminder(app):

    with app.app_context():
        contracts= Contract.query.all()

        print("Running inspection reminder job")

        for contract in contracts:
            print(contract.customer_id)

# remove inspection fee automation
def remove_inspection_fee(app):
    with app.app_context():
        contracts= Contract.query.all()

        today= date.today()

        print("Running inspection fee removal job")

        for contract in contracts:
            # debugging
            print("Inspection End Date:", contract.inspection_end_date)
            print("Today:", today)
            print(
                "Inspection Item ID:",
                contract.inspection_fee_subscription_item_id
            )
            # PYTHON TRUTHY / FALSY
            # Python automatically treats values as: true or false
            # if contract.inspection_fee_subscription_item_id:
            # means if contract.inspection_fee_subscription_item_id is not None: AND not empty
            # contract.inspection_fee_subscription_item_id acts like: Has this automation already been completed?
            if (
                contract.inspection_end_date
                and contract.inspection_end_date <= today 
                and contract.inspection_fee_subscription_item_id):
                print(f"Removing inspection fee for {contract.customer_id}")

                # external APIs can fail
                try:
                    stripe.SubscriptionItem.delete(
                        contract.inspection_fee_subscription_item_id
                    )

                    # means: inspection fee already removed
                    # OTHERWISE AUTOMATIONS LOOP FOREVER
                    # this is called State tracking
                    contract.inspection_fee_subscription_item_id= None

                    db.session.commit()

                    print("Inspection fee removed.")

                except Exception as e:
                    print("Stripe deletion failed: ", e)

            else:
                print("No inspection fee removal needed.")

# Contract expiration automation
def expire_contracts(app):
    with app.app_context(): 
        contracts= Contract.query.all()

        today= date.today()

        print("Running contract expiration job")

        for contract in contracts:
            print("Contract End Date:", contract.contract_end_date)
            print("Today:", today)
            print("Current Status:", contract.status)

            if (
                contract.contract_end_date <= today
                # idempotency
                # state tracking
                and contract.status != 'expired'):
                contract.status= 'expired'

                db.session.commit()

                print(f"Contract expired for {contract.customer_id}")

            else: 
                print("No contract expiration needed. ")


# test retrieve stripe data
def test_stripe_retrieval(app):
    with app.app_context():
        contracts= Contract.query.all()

        for contract in contracts:
            print("Checking contract: ", contract.customer_id)

            subscription= stripe.Subscription.retrieve(
                contract.subscription_id
            )

            print(subscription)
            print(
                "Stripe subscription status: ", subscription['status']
            )

# Reconciliation job (repairs consistency)
# Periodically verify that our DB and Stripe still match.
# webhooks are NOT guaranteed -> could fail
# reconciliation jobs = safety net
def reconcile_subscription_status(app):
    with app.app_context():
        print("Running reconciliation job")
        contracts= Contract.query.all()

        for contract in contracts:
            print("Checking contract: ", contract.customer_id)

            try:
                subscription= stripe.Subscription.retrieve(
                    contract.subscription_id
                )

                stripe_status= subscription['status']

                print("Stripe subscription status: ", stripe_status)
                print("Database subscription status: ", contract.subscription_status)

                # mismatch detection
                if contract.subscription_status != stripe_status:
                    print("Status mismatch detected!!!")

                    contract.subscription_status= stripe_status
                    contract.last_reconciliation_at= datetime.now(timezone.utc)

                    db.session.commit()

                    print("Database corrected. ")
                    print("Updated DB status:", contract.subscription_status
                    )
                else:
                    contract.last_reconciliation_at = datetime.now(timezone.utc)

                    db.session.commit()

                    print("Statuses already synced. ")
            
            except Exception as e:
                print("Reconciliation failed: ", e)

# replay-safe recovery (event-driven state recovery architecture)
def retry_failed_webhooks(app):
    with app.app_context():
        failed_events= WebhookEvent.query.filter_by(
            processed=False
        ).all()

        # len ->how many items inside the thing
        print(f"Found {len(failed_events)} failed webhook(s). ")

        for webhook_event in failed_events:
            print("Retrying: ", webhook_event.stripe_event_id)

            event= webhook_event.payload

            # Dead-letter queue behavior
            # Stop retrying permanently broken jobs
            if webhook_event.retry_count >= 10:
                print("Webhook permanently failed. Manual investigation required. ")

                # Skip the rest of this loop iteration and move to the next item
                continue

            try:
                with db.session.begin():
                    process_webhook_event(event, webhook_event)

                    webhook_event.last_error= None

                print("Webhook replay succeeded. ")

            except Exception as e:
                print("Webhook replay failed: ", e)

                webhook_event.retry_count= webhook_event.retry_count + 1

                webhook_event.last_error= str(e)

                db.session.commit()


# Idempotency mindset
# Running automation multiple times should not break things