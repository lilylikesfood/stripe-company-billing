from datetime import datetime
from dateutil.relativedelta import relativedelta

# This file handles: scheduled business automation
# annual increases
# removing inspection fee
# late fee automation
# overdue balances
# reminders

def run_annual_increase():
    today= datetime.now()

    print("Running annual increase job: ",today)