from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class MenuSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    key = fields.Str()
    label = fields.Str()
    path = fields.Str(allow_none=True)
    icon = fields.Str(allow_none=True)
    show_in_sidebar = fields.Bool()
    order = fields.Int()
    parent_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    children = fields.List(fields.Nested(lambda: MenuSchema()))
