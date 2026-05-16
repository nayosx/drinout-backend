from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class LaundryDeliverySchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(required=True)
    manager_id = fields.Int(required=True)
    driver_id = fields.Int(required=True)
    scheduled_departure_time = fields.DateTime(required=True)
    actual_departure_time = fields.DateTime(allow_none=True)
    customer_expected_time = fields.DateTime(required=True)
    actual_delivery_time = fields.DateTime(allow_none=True)
    status = fields.Str(dump_only=True)
    notes = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
