from marshmallow import Schema, fields, validate


class ServiceCategoryLegacySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    is_active = fields.Bool(load_default=True)
