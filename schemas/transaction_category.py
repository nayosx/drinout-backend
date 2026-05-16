from marshmallow import fields
from schemas.base import BaseSchema

class TransactionCategorySchema(BaseSchema):
    id = fields.Int(dump_only=True)
    category_name = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
