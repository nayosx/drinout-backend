from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class DeliveryStatusLogSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    dispatch_id = fields.Int(required=True)
    status = fields.Str(required=True)
    logged_at = fields.DateTime(dump_only=True)
