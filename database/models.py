# class Contract:

#     def __init__(
#         self,
#         customer_id,
#         start_date,
#         contract_end_date,
#         inspection_end_date
#     ):

#         self.customer_id = customer_id
#         self.start_date = start_date
#         self.contract_end_date = contract_end_date
#         self.inspection_end_date = inspection_end_date

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Contract(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.String(100))

    subscription_id = db.Column(db.String(100))

    subscription_status = db.Column(db.String(50))

    monthly_fee_price_id = db.Column(db.String(100)) 

    inspection_fee_price_id = db.Column(db.String(100))
    
    inspection_fee_subscription_item_id= db.Column(db.String(100))

    status = db.Column(db.String(50), default="active")

    start_date= db.Column(db.Date)

    inspection_end_date = db.Column(db.Date)

    contract_end_date = db.Column(db.Date)

    created_at= db.Column(
        db.DateTime,
        # lambda -> anonymous function, meaning tiny function without a name
        # instead of using default=datetime.now(timezone.utc)
        # Python executes it IMMEDIATELY when app starts.
        # Every row would get same timestamp
        # lambda fixes it -> run this later when row is created
        default=lambda: datetime.now(timezone.utc)
    )

# Webhook Event Logging
# audit trail (if sth breaks, can trace back)
class WebhookEvent(db.Model):
    id= db.Column(db.Integer, primary_key=True)

    stripe_event_id= db.Column(db.String(100), unique=True)

    event_type= db.Column(db.String(100))

    processed= db.Column(db.Boolean, default=False, nullable=False)

    # Replay-safe webhook processing(Idempotent webhook handling)
    processed_at= db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc)
    )

    created_at= db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    last_reconciliation_at= db.Column(db.DateTime)