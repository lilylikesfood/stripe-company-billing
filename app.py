from flask import Flask
from dotenv import load_dotenv
import stripe
import os

from billing.customers import create_customer
from billing.subscriptions import (
    create_product,
    create_monthly_fee,
    create_inspection_fee,
    create_subscription
)
from billing.webhooks import handle_webhook

from database.models import db
from datetime import date
from dateutil.relativedelta import relativedelta
from database.models import Contract

# run jobs in background while Flask server is running
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler.jobs import inspection_reminder, remove_inspection_fee

load_dotenv()

stripe.api_key= os.getenv("STRIPE_SECRET_KEY")

app= Flask(__name__)

# database
# database lives in contracts.db
# use SQLite database file named contracts.db
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///contracts.db'

db.init_app(app)

@app.route("/")
def home():

    customer= create_customer(
        "may13inspectionFeeRemoved",
        "may13inspectionFeeRemoved@example.com"
    )

    product= create_product()
    monthly_fee_price= create_monthly_fee(product.id)
    inspection_fee_price= create_inspection_fee(product.id)
    subscription, inspection_fee_subscription_item_id= create_subscription(
        customer.id,
        monthly_fee_price.id,
        inspection_fee_price.id
    )

    contract = Contract(

    customer_id=customer.id,

    subscription_id=subscription.id,

    monthly_fee_price_id=monthly_fee_price.id,

    inspection_fee_price_id=inspection_fee_price.id,

    inspection_fee_subscription_item_id=inspection_fee_subscription_item_id,

    status="active",

    start_date=date.today(),

    inspection_end_date=
        # date.today() + relativedelta(years=3),
        # testing
        date.today(),

    contract_end_date=
        date.today() + relativedelta(years=50)
)

    db.session.add(contract)
    db.session.commit()

    return subscription.id

@app.route('/webhook', methods=['POST'])
def wevhook():

    return handle_webhook()

@app.route("/contracts")
def contracts():
    
    contracts= Contract.query.all()

    result= ""

    for contract in contracts:
        # """ means multi-line string
        result= result + f"""
        <p>
            Customer: {contract.customer_id}<br>
            Status: {contract.status}<br>
            Subscription: {contract.subscription_id}<br>
            Inspection Ends: {contract.inspection_end_date}<br>
        <p>
        """
    return result

# test dynamic webhook behavior
@app.route("/test-overdue")
def test_overdue():
    contract= Contract.query.first()
    contract.status= "overdue"
    db.session.commit()

    return "Contract marked overdue"

# test canceled behavior
@app.route("/cancel-test")
def cancel_test():
    contract= Contract.query.first()
    contract.status= "canceled"

    db.session.commit()

    return "Contract canceled"

# Scheduler = run code automatically on time
scheduler= BackgroundScheduler()

scheduler.add_job(
    func=inspection_reminder,
    # interval means: repeat forever every X time
    trigger='interval', 
    seconds=10,
    args=[app]
)

# remove_inspection_fee schedular job
scheduler.add_job(
    func=remove_inspection_fee,
    trigger='interval',
    seconds=10,
    args=[app]
)

scheduler.start()

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(port=5000, debug=True)