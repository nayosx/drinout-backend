from marshmallow import Schema, fields

class MenuSchema(Schema):
    id = fields.Int(dump_only=True)
    label = fields.Str()
    path = fields.Str()
    show_in_sidebar = fields.Bool()
    order = fields.Int()
    children = fields.List(fields.Nested(lambda: MenuSchema()))
