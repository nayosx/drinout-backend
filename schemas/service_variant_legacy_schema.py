from marshmallow import Schema, fields, validate


class ServiceVariantLegacySchema(Schema):
    id = fields.Int(dump_only=True)
    service_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    price = fields.Decimal(required=True, as_string=True, places=2)
    is_active = fields.Bool(load_default=True)
