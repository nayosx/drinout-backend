from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin


class ServiceCategorySchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    code = fields.Str(required=True, validate=validate.Length(max=50))
    name = fields.Str(required=True, validate=validate.Length(max=100))
    description = fields.Str(allow_none=True)
    sort_order = fields.Int(allow_none=True)
    is_active = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
