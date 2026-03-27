from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin
from schemas.weight_pricing_tier_schema import WeightPricingTierSchema


WEIGHT_PRICING_STRATEGIES = [
    "MAX_REVENUE",
    "BEST_TIER_FIT",
    "BASE_PLUS_EXTRA",
    "CUSTOMER_BEST_PRICE",
    "PROMOTIONAL_UPGRADE",
    "FORCE_UPGRADE_FROM_WEIGHT",
]

ROUND_MODES = ["exact", "ceil", "floor"]


class WeightPricingProfileSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(max=120))
    is_active = fields.Bool(load_default=True)
    strategy = fields.Str(required=True, validate=validate.OneOf(WEIGHT_PRICING_STRATEGIES))
    extra_lb_price = fields.Decimal(required=True, as_string=True, places=2)
    auto_upgrade_enabled = fields.Bool(load_default=False)
    auto_upgrade_margin = fields.Decimal(load_default="0.00", as_string=True, places=2)
    force_upgrade_from_lb = fields.Decimal(as_string=True, places=2, allow_none=True)
    compare_all_tiers = fields.Bool(load_default=True)
    round_mode = fields.Str(load_default="exact", validate=validate.OneOf(ROUND_MODES))
    allow_manual_override = fields.Bool(load_default=True)
    notes = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    tiers = fields.Nested(WeightPricingTierSchema, many=True, dump_only=True)
