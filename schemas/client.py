from marshmallow import Schema, fields

# Schema resumido para listado
class ClientShortSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()

class ClientAddressNoUpdateSchema(Schema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int()
    address_text = fields.Str()
    latitude = fields.Decimal(as_string=True)
    longitude = fields.Decimal(as_string=True)
    map_link = fields.Str()
    image_path = fields.Str()
    is_primary = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

class ClientPhoneNoUpdateSchema(Schema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int()
    phone_number = fields.Str()
    description = fields.Str()
    is_primary = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

class ClientDetailSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    document_id = fields.Str()
    is_deleted = fields.Bool()
    created_by = fields.Int()
    updated_by = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    addresses = fields.Nested(ClientAddressNoUpdateSchema, many=True)
    phones = fields.Nested(ClientPhoneNoUpdateSchema, many=True)
