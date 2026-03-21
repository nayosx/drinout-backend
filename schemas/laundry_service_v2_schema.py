from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin
from schemas.client_schema import ClientDetailSchema, ClientAddressNoUpdateSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_schema import UserSchema
from schemas.laundry_service_log_schema import LaundryServiceLogSchema
from schemas.laundry_service_item_schema import LaundryServiceItemInputSchema, LaundryServiceItemSchema
from schemas.laundry_service_extra_schema import LaundryServiceExtraInputSchema, LaundryServiceExtraSchema


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
    transaction_id = fields.Int(allow_none=True)
    weight_lb = fields.Float(allow_none=True)
    notes = fields.Str(allow_none=True)
    items = fields.List(fields.Nested(LaundryServiceItemInputSchema), load_default=list)
    extras = fields.List(fields.Nested(LaundryServiceExtraInputSchema), load_default=list)


class LaundryServiceV2Schema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int(required=True)
    client_address_id = fields.Int(required=True)
    scheduled_pickup_at = fields.DateTime(required=True)
    pending_order = fields.Int(dump_only=True, allow_none=True)
    status = fields.Str(required=True)
    service_label = fields.Str(required=True)
    transaction_id = fields.Int(allow_none=True)
    weight_lb = fields.Float(allow_none=True)
    notes = fields.Str(allow_none=True)
    created_by_user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    client = fields.Nested(ClientDetailSchema, only=["id", "name"], dump_only=True)
    client_address = fields.Nested(ClientAddressNoUpdateSchema, dump_only=True, allow_none=True)
    transaction = fields.Nested(TransactionSchema, dump_only=True, allow_none=True)
    created_by_user = fields.Nested(UserSchema, dump_only=True, allow_none=True)
    logs = fields.List(fields.Nested(LaundryServiceLogSchema), dump_only=True)
    items = fields.List(fields.Nested(LaundryServiceItemSchema), dump_only=True)
    extras = fields.List(fields.Nested(LaundryServiceExtraSchema), dump_only=True)
    items_total = fields.Method("get_items_total", dump_only=True)
    extras_total = fields.Method("get_extras_total", dump_only=True)
    grand_total = fields.Method("get_grand_total", dump_only=True)

    def _safe_sum(self, rows):
        total = 0.0
        for row in rows:
            subtotal = getattr(row, "subtotal", None)
            if subtotal is not None:
                total += float(subtotal)
        return round(total, 2)

    def get_items_total(self, obj):
        return self._safe_sum(getattr(obj, "items", []))

    def get_extras_total(self, obj):
        return self._safe_sum(getattr(obj, "extras", []))

    def get_grand_total(self, obj):
        return round(self.get_items_total(obj) + self.get_extras_total(obj), 2)
