from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin

SURCHARGE_TYPES = ["PERCENT", "FIXED"]


class PaymentTypeSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    code = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    surcharge_type = fields.Str(required=True, validate=validate.OneOf(SURCHARGE_TYPES))
    surcharge_value = fields.Decimal(required=True, as_string=True, places=4)
    is_active = fields.Bool(load_default=True)
    sort_order = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
