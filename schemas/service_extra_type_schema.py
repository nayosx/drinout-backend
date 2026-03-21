from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin


class ServiceExtraTypeSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    code = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    unit_label = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    default_unit_price = fields.Float(allow_none=True)
    active = fields.Bool(load_default=True)
    display_order = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
