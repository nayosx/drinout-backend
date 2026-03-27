from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin


class DeliveryZonePriceSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    delivery_zone_id = fields.Int(required=True)
    fee_amount = fields.Decimal(required=True, as_string=True, places=2)
    is_active = fields.Bool(load_default=True)
    effective_from = fields.DateTime(load_default=None, allow_none=True)
    effective_to = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class DeliveryZoneSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    code = fields.Str(required=True, validate=validate.Length(max=80))
    name = fields.Str(required=True, validate=validate.Length(max=150))
    description = fields.Str(allow_none=True)
    is_active = fields.Bool(load_default=True)
    current_fee = fields.Decimal(as_string=True, places=2, allow_none=True, load_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    prices = fields.Nested(DeliveryZonePriceSchema, many=True, dump_only=True)
