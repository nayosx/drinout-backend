from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin
from schemas.order_extra_item_schema import OrderExtraItemInputSchema, OrderExtraItemSchema
from schemas.order_item_schema import OrderItemInputSchema, OrderItemSchema


ORDER_STATUSES = [
    "DRAFT",
    "QUOTED",
    "CONFIRMED",
    "IN_PROCESS",
    "READY",
    "DELIVERED",
    "CANCELLED",
]


class OrderCreateSchema(Schema):
    client_id = fields.Int(required=True)
    client_address_id = fields.Int(allow_none=True)
    pricing_profile_id = fields.Int(allow_none=True)
    delivery_zone_id = fields.Int(allow_none=True)
    delivery_fee_final = fields.Decimal(as_string=True, places=2, allow_none=True)
    delivery_fee_override_reason = fields.Str(allow_none=True)
    status = fields.Str(load_default="CONFIRMED", validate=validate.OneOf(ORDER_STATUSES))
    global_discount_amount = fields.Decimal(load_default="0.00", as_string=True, places=2)
    global_discount_reason = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    charged_by_user_id = fields.Int(allow_none=True)
    items = fields.List(fields.Nested(OrderItemInputSchema), required=True, validate=validate.Length(min=1))
    extras = fields.List(fields.Nested(OrderExtraItemInputSchema), load_default=list)


class OrderPatchSchema(Schema):
    status = fields.Str(validate=validate.OneOf(ORDER_STATUSES))
    delivery_fee_final = fields.Decimal(as_string=True, places=2, allow_none=True)
    delivery_fee_override_reason = fields.Str(allow_none=True)
    global_discount_amount = fields.Decimal(as_string=True, places=2)
    global_discount_reason = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    charged_by_user_id = fields.Int(allow_none=True)


class OrderSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int(required=True)
    client_address_id = fields.Int(allow_none=True)
    pricing_profile_id = fields.Int(allow_none=True)
    delivery_zone_id = fields.Int(allow_none=True)
    delivery_zone_price_id = fields.Int(allow_none=True)
    status = fields.Str(validate=validate.OneOf(ORDER_STATUSES))
    service_subtotal = fields.Decimal(as_string=True, places=2, dump_only=True)
    extras_subtotal = fields.Decimal(as_string=True, places=2, dump_only=True)
    delivery_fee_suggested = fields.Decimal(as_string=True, places=2, dump_only=True)
    delivery_fee_final = fields.Decimal(as_string=True, places=2)
    delivery_fee_override_by_user_id = fields.Int(allow_none=True, dump_only=True)
    delivery_fee_override_reason = fields.Str(allow_none=True)
    global_discount_amount = fields.Decimal(as_string=True, places=2)
    global_discount_reason = fields.Str(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, dump_only=True)
    notes = fields.Str(allow_none=True)
    charged_by_user_id = fields.Int(allow_none=True)
    created_by_user_id = fields.Int(dump_only=True)
    updated_by_user_id = fields.Int(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.Nested(OrderItemSchema, many=True, dump_only=True)
    extra_items = fields.Nested(OrderExtraItemSchema, many=True, dump_only=True)
