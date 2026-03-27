from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin
from schemas.service_category_schema import ServiceCategorySchema
from schemas.service_price_option_schema import ServicePriceOptionSchema


PRICING_MODES = ["FIXED", "WEIGHT"]


class CatalogServiceSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    category_id = fields.Int(required=True)
    code = fields.Str(required=True, validate=validate.Length(max=80))
    name = fields.Str(required=True, validate=validate.Length(max=150))
    pricing_mode = fields.Str(required=True, validate=validate.OneOf(PRICING_MODES))
    unit_label = fields.Str(load_default="unidad", validate=validate.Length(max=30))
    description = fields.Str(allow_none=True)
    is_active = fields.Bool(load_default=True)
    allow_manual_price_override = fields.Bool(load_default=True)
    allow_item_discount = fields.Bool(load_default=True)
    sort_order = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    category = fields.Nested(ServiceCategorySchema, dump_only=True)
    price_options = fields.Nested(ServicePriceOptionSchema, many=True, dump_only=True)
