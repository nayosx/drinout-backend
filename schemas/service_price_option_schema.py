from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin


class ServicePriceOptionSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    service_id = fields.Int(required=True)
    label = fields.Str(required=True, validate=validate.Length(max=100))
    suggested_price = fields.Decimal(required=True, as_string=True, places=2)
    sort_order = fields.Int(allow_none=True)
    is_active = fields.Bool(load_default=True)
    notes = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
