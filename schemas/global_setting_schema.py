from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin


GLOBAL_SETTING_VALUE_TYPES = ["STRING", "DECIMAL", "INT", "BOOL", "JSON"]


class GlobalSettingSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    key = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    description = fields.Str(allow_none=True, validate=validate.Length(max=255))
    value_type = fields.Str(
        load_default="STRING",
        validate=validate.OneOf(GLOBAL_SETTING_VALUE_TYPES),
    )
    value = fields.Str(required=True)
    is_active = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
