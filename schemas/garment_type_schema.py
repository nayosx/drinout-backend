from marshmallow import Schema, fields, validate


class GarmentTypeSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    icon = fields.Str(allow_none=True, validate=validate.Length(max=30))
    is_frequent = fields.Bool(load_default=False)
