from datetime import datetime
from dateutil.relativedelta import relativedelta

from database.models import Contract
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
    