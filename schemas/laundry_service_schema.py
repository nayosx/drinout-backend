from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin

from schemas.client_schema import ClientDetailSchema, ClientSchema, ClientShortSchema, ClientWithPhonesSchema
from schemas.client_schema import ClientAddressNoUpdateSchema
from schemas.laundry_service_log_schema import LaundryServiceLogSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_schema import UserSchema

class LaundryServiceSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)

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
            "CANCELLED"
        ])
    )


    service_label = fields.Str(
        required=True,
        validate=validate.OneOf(["NORMAL", "EXPRESS"])
    )

    transaction_id = fields.Int(allow_none=True)

    created_by_user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class LaundryServiceGetSchema(LaundryServiceSchema):
    client = fields.Nested(ClientDetailSchema, only=["id", "name"], dump_only=True)
    client_address = fields.Nested(ClientAddressNoUpdateSchema, dump_only=True, allow_none=True)
    transaction = fields.Nested(TransactionSchema, dump_only=True, allow_none=True)
    created_by = fields.Nested(UserSchema, dump_only=True, allow_none=True)

class LaundryServiceAllSchema(LaundryServiceGetSchema):
    logs = fields.List(fields.Nested(LaundryServiceLogSchema), dump_only=True)


class LaundryServiceLiteSchema(LaundryServiceSchema):
    id = fields.Int()
    scheduled_pickup_at = fields.DateTime()
    status = fields.Str()
    service_label = fields.Str()
    client = fields.Nested(ClientShortSchema, only=["id", "name"])
    created_by_user = fields.Nested(UserSchema, only=["name"])


class LaundryServiceDetailSchema(LaundryServiceSchema):
    id = fields.Int()
    scheduled_pickup_at = fields.DateTime()
    status = fields.Str()
    service_label = fields.Str()
    client = fields.Nested(ClientWithPhonesSchema)
    client_address = fields.Nested(ClientAddressNoUpdateSchema)
    transaction = fields.Nested(TransactionSchema, allow_none=True)
    created_by_user = fields.Nested(UserSchema, only=["name"])

class LaundryServiceCompactSchema(LaundryServiceSchema):
    id = fields.Int()
    service_label = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime()
    created_by_user = fields.Nested("UserSchema", only=("name",))
    created_by_user_id = fields.Int()
    client = fields.Nested("ClientDetailSchema", only=("id", "name"))
    client_id = fields.Int()
    client_address_id = fields.Int()
    client_address = fields.Nested(ClientAddressNoUpdateSchema, only=("id", "client_id", "address_text"))
    has_transaction = fields.Method("get_has_transaction")

    def get_has_transaction(self, obj):
        return obj.transaction_id is not None

