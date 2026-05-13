import stripe

def create_product():

    product = stripe.Product.create(
        name="flower"
    )

    return product

def create_monthly_price(product_id):

    price = stripe.Price.create(
        unit_amount=10000,
        currency="cad",
        recurring={"interval": "month"},
        product=product_id
    )

    return price

def create_inspection_price(product_id):

    price= stripe.Price.create(
        unit_amount=25000,
        currency="cad",
        recurring={"interval": "year"},
        product=product_id
    )

    return price

def create_subscription(customer_id, monthly_price_id, inspection_price_id):

    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[
            {
                "price": monthly_price_id
            },
            {
                "price": inspection_price_id
            }
        ],

        # TEMPORARY TEST MODE SOLUTION
        payment_behavior="default_incomplete"
    )

    return subscription