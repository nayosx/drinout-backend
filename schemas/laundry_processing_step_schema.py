from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class LaundryProcessingStepSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(required=True)
    step_type = fields.Str(required=True)
    started_by_user_id = fields.Int(dump_only=True)
    completed_by_user_id = fields.Int(allow_none=True)
    started_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(allow_none=True)
    notes = fields.Str(allow_none=True)
