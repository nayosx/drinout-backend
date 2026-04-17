from marshmallow import Schema, fields


class OrderItemSchema(Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(required=True)
    service_id = fields.Int(required=True)
    service_variant_id = fields.Int(allow_none=True)
    garment_type_id = fields.Int(allow_none=True)
    quantity = fields.Decimal(required=True, as_string=True, places=2)
    unit_catalog_price = fields.Decimal(allow_none=True, as_string=True, places=2)
    catalog_price = fields.Decimal(required=True, as_string=True, places=2)
    applied_price = fields.Decimal(required=True, as_string=True, places=2)
    is_friendly_discount = fields.Bool(load_default=False)
    calculation_snapshot = fields.Raw(allow_none=True)
