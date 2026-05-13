import stripe

def list_customer_invoices(customer_id):

    invoices= stripe.Invoice.list(
        customer=customer_id, 
        limit=10
    )

    return invoices