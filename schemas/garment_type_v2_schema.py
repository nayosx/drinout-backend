from marshmallow import fields, validate
from schemas.base import BaseSchema


class GarmentTypeV2Schema(BaseSchema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
