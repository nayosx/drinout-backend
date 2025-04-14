from marshmallow import Schema, fields

class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    description = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user_name = fields.String(attribute="user.name")

class TaskViewSchema(Schema):
    id = fields.Int(dump_only=True)
    task_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    viewed_at = fields.DateTime(dump_only=True)
