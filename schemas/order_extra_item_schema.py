from marshmallow import Schema, fields

from schemas.base import LocalDateTimeMixin


class OrderExtraItemInputSchema(Schema):
    extra_id = fields.Int(required=True)
    quantity = fields.Decimal(load_default="1.00", as_string=True, places=2)
    final_unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    discount_amount = fields.Decimal(load_default="0.00", as_string=True, places=2)
    notes = fields.Str(allow_none=True)


class OrderExtraItemSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int(dump_only=True)
    extra_id = fields.Int(required=True)
    extra_name_snapshot = fields.Str(dump_only=True)
    unit_label_snapshot = fields.Str(dump_only=True)
    quantity = fields.Decimal(as_string=True, places=2)
    suggested_unit_price = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    final_unit_price = fields.Decimal(as_string=True, places=2)
    discount_amount = fields.Decimal(as_string=True, places=2)
    subtotal_before_discount = fields.Decimal(as_string=True, places=2, dump_only=True)
    subtotal_after_discount = fields.Decimal(as_string=True, places=2, dump_only=True)
    notes = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
