from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from database.models import Contract,db

import stripe
# from flask import current_app
# error: circular import
# from app import app

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
            if (contract.inspection_end_date <= today and contract.inspection_fee_subscription_item_id):
                print(f"Removing inspection fee for {contract.customer_id}")
            else:
                print("No inspection fee removal needed.")

                stripe.SubscriptionItem.delete(
                    contract.inspection_fee_subscription_item_id
                )

                # means: inspection fee already removed
                # OTHERWISE AUTOMATIONS LOOP FOREVER
                # this is called State tracking
                contract.inspection_fee_subscription_item_id= None

                db.session.commit()

                print("Inspection fee removed.")


# Idempotency mindset
# Running automation multiple times should not break things