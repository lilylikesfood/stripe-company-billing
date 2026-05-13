import stripe

def create_product():

    product = stripe.Product.create(
        name="May13_inspectionFeeRemoved"
    )

    return product

def create_monthly_fee(product_id):

    price = stripe.Price.create(
        unit_amount=10000,
        currency="cad",
        recurring={"interval": "month"},
        product=product_id
    )

    return price

def create_inspection_fee(product_id):

    price= stripe.Price.create(
        unit_amount=25000,
        currency="cad",
        recurring={"interval": "year"},
        product=product_id
    )

    return price

def create_subscription(customer_id, monthly_fee_price_id, inspection_fee_price_id):

    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[
            {"price": monthly_fee_price_id},
            {"price": inspection_fee_price_id}
        ],

        # TEMPORARY TEST MODE SOLUTION
        payment_behavior="default_incomplete"
    )

    inspection_fee_subscription_item_id= None

    for item in subscription["items"]["data"]:
        if item["price"]["id"] == inspection_fee_price_id:
            inspection_fee_subscription_item_id= item["id"]

    print(subscription["items"]["data"])

    return subscription, inspection_fee_subscription_item_id