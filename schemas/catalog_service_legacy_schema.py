from marshmallow import Schema, fields, validate


PRICING_MODES = ["FIXED", "WEIGHT", "DELIVERY"]


class CatalogServiceLegacySchema(Schema):
    id = fields.Int(dump_only=True)
    category_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    pricing_mode = fields.Str(
        load_default="FIXED",
        validate=validate.OneOf(PRICING_MODES),
    )
    is_active = fields.Bool(load_default=True)
