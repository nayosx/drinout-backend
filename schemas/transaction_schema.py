# schemas/transaction_schema.py

from marshmallow import Schema, fields, validate
from models.transaction import Transaction
from schemas.base import LocalDateTimeMixin

class TransactionSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    transaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(["IN","OUT"])
    )
    payment_type_id = fields.Int(required=True)
    category_id = fields.Int(allow_none=True)
    detail = fields.Str(allow_none=True)
    amount = fields.Decimal(as_string=True, required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    client_id = fields.Int(allow_none=True)
    client_name = fields.Str(allow_none=True)

    user_name = fields.String(attribute="user.name")
    payment_type_name = fields.String(attribute="payment_type.name")
    category_name = fields.String(attribute="category.category_name")
    client_name = fields.String(attribute="client.name")