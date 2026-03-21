from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin


class GarmentTypeV2Schema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    icon = fields.Str(allow_none=True, validate=validate.Length(max=30))
    is_frequent = fields.Bool(load_default=False)
    category = fields.Str(
        required=True,
        validate=validate.OneOf(["CLOTHING", "BEDDING", "FOOTWEAR", "PLUSH", "RUG", "HOUSEHOLD"]),
    )
    active = fields.Bool(load_default=True)
    default_unit_type = fields.Str(
        required=True,
        validate=validate.OneOf(["UNIT", "PAIR"]),
    )
    default_unit_price = fields.Float(allow_none=True)
    display_order = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
