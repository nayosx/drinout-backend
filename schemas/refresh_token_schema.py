from marshmallow import fields
from schemas.base import BaseSchema

class RefreshTokenSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    jti = fields.Str()
    user_id = fields.Int()
    expires_at = fields.DateTime()
    revoked = fields.Bool()
    created_at = fields.DateTime()
