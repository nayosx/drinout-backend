# schemas/user_schema.py
from marshmallow import Schema, fields, validate
from models.user import User
from schemas.base import LocalDateTimeMixin

class UserSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50)
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=6)
    )
    role_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50)
    )
    phone = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=20)
    )
