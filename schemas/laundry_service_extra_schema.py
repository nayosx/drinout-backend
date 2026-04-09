from marshmallow import Schema, fields


class LaundryServiceExtraSchema(Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(required=True)
    extra_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    unit_price = fields.Decimal(required=True, as_string=True, places=2)
    subtotal = fields.Decimal(required=True, as_string=True, places=2)
    is_courtesy = fields.Bool(load_default=False)
