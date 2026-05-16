from marshmallow import fields
from schemas.base import BaseSchema

class DeliveryStatusLogSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    dispatch_id = fields.Int(required=True)
    status = fields.Str(required=True)
    logged_at = fields.DateTime(dump_only=True)
