from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin
from schemas.catalog_service_schema import PRICING_MODES
from schemas.order_weight_pricing_snapshot_schema import OrderWeightPricingSnapshotSchema


class OrderItemInputSchema(Schema):
    service_id = fields.Int(required=True)
    suggested_price_option_id = fields.Int(allow_none=True)
    quantity = fields.Decimal(load_default="1.00", as_string=True, places=2)
    weight_lb = fields.Decimal(as_string=True, places=2, allow_none=True)
    final_unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    discount_amount = fields.Decimal(load_default="0.00", as_string=True, places=2)
    notes = fields.Str(allow_none=True)
    manual_price_override_reason = fields.Str(allow_none=True)


class OrderItemSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int(dump_only=True)
    service_id = fields.Int(required=True)
    suggested_price_option_id = fields.Int(allow_none=True)
    service_name_snapshot = fields.Str(dump_only=True)
    category_name_snapshot = fields.Str(dump_only=True)
    pricing_mode = fields.Str(validate=validate.OneOf(PRICING_MODES), dump_only=True)
    quantity = fields.Decimal(as_string=True, places=2)
    weight_lb = fields.Decimal(as_string=True, places=2, allow_none=True)
    unit_label_snapshot = fields.Str(dump_only=True)
    suggested_price_label_snapshot = fields.Str(allow_none=True, dump_only=True)
    suggested_unit_price = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    recommended_unit_price = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    final_unit_price = fields.Decimal(as_string=True, places=2)
    manual_price_override_by_user_id = fields.Int(allow_none=True, dump_only=True)
    manual_price_override_reason = fields.Str(allow_none=True)
    discount_amount = fields.Decimal(as_string=True, places=2)
    subtotal_before_discount = fields.Decimal(as_string=True, places=2, dump_only=True)
    subtotal_after_discount = fields.Decimal(as_string=True, places=2, dump_only=True)
    notes = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    weight_pricing_snapshot = fields.Nested(OrderWeightPricingSnapshotSchema, dump_only=True)
