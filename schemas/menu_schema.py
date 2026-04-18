from marshmallow import Schema, fields
from schemas.base import LocalDateTimeMixin

class MenuSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    label = fields.Str()
    path = fields.Str()
    show_in_sidebar = fields.Bool()
    order = fields.Int()
    parent_id = fields.Int(allow_none=True)
    children = fields.List(fields.Nested(lambda: MenuSchema()))
