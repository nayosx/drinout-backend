from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class TransactionCategorySchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    category_name = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
