from datetime import date

class Reconciliation:
    def __init__(
        self,
        id,
        product_id,
        previous_quantity,
        physical_quantity,
    ):
        self.id = id
        self.product_id = product_id
        self.previous_quantity = previous_quantity
        self.physical_quantity = physical_quantity
        self.adjustment = physical_quantity - previous_quantity
        self.reconciliation_date = date.today()

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "previous_quantity": self.previous_quantity,
            "physical_quantity": self.physical_quantity,
            "adjustment": self.adjustment,
            "reconciliation_date": (
                self.reconciliation_date.isoformat()
            ),
        }
