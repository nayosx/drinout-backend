from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class LaundryActivityLogSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(required=True)
    user_id = fields.Int(allow_none=True)
    action = fields.Str(required=True)
    previous_status = fields.Str(allow_none=True)
    new_status = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
