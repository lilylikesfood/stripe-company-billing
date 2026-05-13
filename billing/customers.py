import stripe

def create_customer(name, email):

    customer= stripe.Customer.create(
        name=name,
        email=email
    )

    return customer