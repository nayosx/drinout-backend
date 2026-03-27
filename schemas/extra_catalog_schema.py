from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin


class ExtraCatalogSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    code = fields.Str(required=True, validate=validate.Length(max=80))
    name = fields.Str(required=True, validate=validate.Length(max=150))
    unit_label = fields.Str(load_default="unidad", validate=validate.Length(max=30))
    suggested_unit_price = fields.Decimal(required=True, as_string=True, places=2)
    is_active = fields.Bool(load_default=True)
    sort_order = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
