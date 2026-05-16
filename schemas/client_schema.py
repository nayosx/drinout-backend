from marshmallow import fields
from schemas.base import BaseSchema
from schemas.client_service_type_surcharge_rule_schema import (
    ClientServiceTypeSurchargeRuleSchema,
)

# ----------------------------
# Cliente completo
# ----------------------------
class ClientSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str()
    document_id = fields.Str()
    is_deleted = fields.Bool()
    created_by = fields.Int()
    updated_by = fields.Int()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

# ----------------------------
# Cliente resumen (solo id y name)
# ----------------------------
class ClientShortSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    name = fields.Str()

# ----------------------------
# Dirección completa (creación/edición)
# ----------------------------
class ClientAddressSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int(required=True)
    address_text = fields.Str(required=True)
    latitude = fields.Decimal(as_string=True)
    longitude = fields.Decimal(as_string=True)
    map_link = fields.Str()
    image_path = fields.Str()
    is_primary = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

# ----------------------------
# Dirección sin fechas de actualización
# ----------------------------
class ClientAddressNoUpdateSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int()
    address_text = fields.Str()
    latitude = fields.Decimal(as_string=True)
    longitude = fields.Decimal(as_string=True)
    map_link = fields.Str()
    image_path = fields.Str()
    is_primary = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

# ----------------------------
# Teléfono completo (creación/edición)
# ----------------------------
class ClientPhoneSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int(required=True)
    phone_number = fields.Str(required=True)
    description = fields.Str()
    is_primary = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

# ----------------------------
# Teléfono sin fechas de actualización
# ----------------------------
class ClientPhoneNoUpdateSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int()
    phone_number = fields.Str()
    description = fields.Str()
    is_primary = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

# ----------------------------
# Cliente detallado con relaciones
# ----------------------------
class ClientDetailSchema(BaseSchema):
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
    service_type_surcharge_rules = fields.Nested(
        ClientServiceTypeSurchargeRuleSchema,
        many=True,
    )


class ClientWithPhonesSchema(BaseSchema):
    id = fields.Int()
    name = fields.Str()
    email = fields.Str()
    document_id = fields.Str()
    is_deleted = fields.Bool()
    phones = fields.Nested(ClientPhoneNoUpdateSchema, many=True)
