from marshmallow import Schema, fields

from schemas.base import LocalDateTimeMixin


class OrderWeightPricingSnapshotSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int(dump_only=True)
    order_item_id = fields.Int(dump_only=True)
    pricing_profile_id = fields.Int(allow_none=True)
    pricing_profile_name_snapshot = fields.Str(dump_only=True)
    strategy_applied = fields.Str(dump_only=True)
    weight_lb = fields.Decimal(as_string=True, dump_only=True, places=2)
    selected_tier_id = fields.Int(allow_none=True, dump_only=True)
    selected_tier_max_weight_lb = fields.Decimal(as_string=True, dump_only=True, places=2, allow_none=True)
    selected_base_price = fields.Decimal(as_string=True, dump_only=True, places=2, allow_none=True)
    recommended_price = fields.Decimal(as_string=True, dump_only=True, places=2)
    final_price = fields.Decimal(as_string=True, dump_only=True, places=2)
    override_applied = fields.Bool(dump_only=True)
    override_by_user_id = fields.Int(allow_none=True, dump_only=True)
    override_reason = fields.Str(allow_none=True, dump_only=True)
    allow_manual_override = fields.Bool(dump_only=True)
    decision_reason = fields.Str(dump_only=True)
    options_evaluated_json = fields.Str(dump_only=True)
    lowest_valid_price = fields.Decimal(as_string=True, dump_only=True, places=2)
    highest_valid_price = fields.Decimal(as_string=True, dump_only=True, places=2)
    difference_selected_vs_lowest = fields.Decimal(as_string=True, dump_only=True, places=2)
    difference_selected_vs_highest = fields.Decimal(as_string=True, dump_only=True, places=2)
    created_at = fields.DateTime(dump_only=True)
