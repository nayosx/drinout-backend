from marshmallow import Schema, fields, validate


class ExtraSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    default_price = fields.Decimal(required=True, as_string=True, places=2)
    is_active = fields.Bool(load_default=True)
