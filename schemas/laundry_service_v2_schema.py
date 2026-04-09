from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin
from schemas.client_schema import ClientDetailSchema, ClientAddressNoUpdateSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_schema import UserSchema


FULFILLMENT_TYPES = ["WALK_IN", "DELIVERY", "PICKUP_DELIVERY"]


class LaundryServiceV2UpsertSchema(Schema):
    client_id = fields.Int(required=True)
    client_address_id = fields.Int(required=True)
    scheduled_pickup_at = fields.DateTime(required=True)
    status = fields.Str(
        required=True,
        validate=validate.OneOf([
            "PENDING",
            "STARTED",
            "IN_PROGRESS",
            "READY_FOR_DELIVERY",
            "DELIVERED",
            "CANCELLED",
        ]),
    )
    service_label = fields.Str(
        required=True,
        validate=validate.OneOf(["NORMAL", "EXPRESS"]),
    )
    fulfillment_type = fields.Str(
        load_default="WALK_IN",
        validate=validate.OneOf(FULFILLMENT_TYPES),
    )
    transaction_id = fields.Int(allow_none=True)
    notes = fields.Str(allow_none=True)


class LaundryServiceV2Schema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int(required=True)
    client_address_id = fields.Int(required=True)
    scheduled_pickup_at = fields.DateTime(required=True)
    pending_order = fields.Int(dump_only=True, allow_none=True)
    status = fields.Str(required=True)
    service_label = fields.Str(required=True)
    fulfillment_type = fields.Str(required=True)
    transaction_id = fields.Int(allow_none=True)
    notes = fields.Str(allow_none=True)
    created_by_user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    client = fields.Nested(ClientDetailSchema, only=["id", "name"], dump_only=True)
    client_address = fields.Nested(ClientAddressNoUpdateSchema, dump_only=True, allow_none=True)
    transaction = fields.Nested(TransactionSchema, dump_only=True, allow_none=True)
    created_by_user = fields.Nested(UserSchema, dump_only=True, allow_none=True)
