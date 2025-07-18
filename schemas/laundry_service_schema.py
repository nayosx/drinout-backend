from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin

class LaundryServiceSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)

    client_id = fields.Int(required=True)
    client_address_id = fields.Int(required=True)
    scheduled_pickup_at = fields.DateTime(required=True)

    status = fields.Str(
        required=True,
        validate=validate.OneOf([
            "PENDING",
            "IN_PROGRESS",
            "READY_FOR_DELIVERY",
            "DELIVERED",
            "CANCELLED"
        ])
    )

    service_label = fields.Str(
        required=True,
        validate=validate.OneOf(["NORMAL", "EXPRESS"])
    )

    detail = fields.Str(allow_none=True)
    transaction_id = fields.Int(allow_none=True)

    created_by_user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
