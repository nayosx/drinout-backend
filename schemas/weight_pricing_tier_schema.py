from marshmallow import Schema, fields

from schemas.base import LocalDateTimeMixin


class WeightPricingTierSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    profile_id = fields.Int(required=True)
    max_weight_lb = fields.Decimal(required=True, as_string=True, places=2)
    price = fields.Decimal(required=True, as_string=True, places=2)
    sort_order = fields.Int(required=True)
    is_active = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
