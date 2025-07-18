from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class RefreshTokenSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    jti = fields.Str()
    user_id = fields.Int()
    expires_at = fields.DateTime()
    revoked = fields.Bool()
    created_at = fields.DateTime()
