from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin


class GarmentTypeV2Schema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
