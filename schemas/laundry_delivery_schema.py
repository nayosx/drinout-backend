from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class LaundryDeliverySchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(required=True)
    created_by_user_id = fields.Int(dump_only=True)
    assigned_to_user_id = fields.Int(allow_none=True)
    scheduled_delivery_at = fields.DateTime(required=True)
    delivered_at = fields.DateTime(allow_none=True)
    status = fields.Str(dump_only=True)
    cancel_note = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
