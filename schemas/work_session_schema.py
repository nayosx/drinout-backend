from marshmallow import fields
from schemas.base import BaseSchema

class WorkSessionSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    login_time = fields.DateTime(dump_only=True)
    logout_time = fields.DateTime(allow_none=True)
    status = fields.Str()
    comments = fields.Str(allow_none=True)
    idempotency_key = fields.Str(dump_only=True)