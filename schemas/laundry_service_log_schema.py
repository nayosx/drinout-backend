from marshmallow import Schema, fields, validate
from schemas.user_schema import UserSchema

class LaundryServiceLogSchema(Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(required=True)

    status = fields.Str(
        required=True,
        validate=validate.OneOf([
            "PENDING", "STARTED", "IN_PROGRESS", "READY_FOR_DELIVERY", "DELIVERED", "CANCELLED"
        ])
    )

    detail = fields.Str(required=True)
    created_by_user_id = fields.Int(dump_only=True)
    created_by = fields.Nested(UserSchema, only=["id", "name"], dump_only=True)
    created_at = fields.DateTime(dump_only=True)
