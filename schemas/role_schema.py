# schemas/role_schema.py
from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class RoleSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
