from flask import Flask
from dotenv import load_dotenv
import stripe
import os

from billing.customers import create_customer
from billing.subscriptions import (
    create_product,
    create_monthly_price,
    create_inspection_price,
    create_subscription
)
from billing.webhooks import handle_webhook

from database.models import db
from datetime import date
from dateutil.relativedelta import relativedelta
from database.models import Contract

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
        "dataBASE",
        "dataBASE@example.com"
    )

    product= create_product()
    monthly_price= create_monthly_price(product.id)
    inspection_price= create_inspection_price(product.id)
    subscription= create_subscription(
        customer.id,
        monthly_price.id,
        inspection_price.id
    )

    contract = Contract(

    customer_id=customer.id,

    subscription_id=subscription.id,

    monthly_price_id=monthly_price.id,

    inspection_price_id=inspection_price.id,

    status="active",

    start_date=date.today(),

    inspection_end_date=
        date.today() + relativedelta(years=3),

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

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(port=5000)