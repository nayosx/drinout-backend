from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from models.transaction import Transaction

class TransactionSchema(Schema):
    id = fields.Int(dump_only=True)

    user_id = fields.Int(required=True)
    transaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(["IN","OUT"], error="transaction_type must be 'IN' or 'OUT'")
    )
    payment_type_id = fields.Int(required=True)
    detail = fields.Str(allow_none=True)
    amount = fields.Decimal(as_string=True, required=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
