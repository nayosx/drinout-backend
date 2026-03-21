from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin
from schemas.service_extra_type_schema import ServiceExtraTypeSchema


class LaundryServiceExtraInputSchema(Schema):
    service_extra_type_id = fields.Int(required=True)
    quantity = fields.Float(required=True, validate=validate.Range(min=0.01))
    unit_price = fields.Float(allow_none=True)
    notes = fields.Str(allow_none=True)


class LaundryServiceExtraSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    service_extra_type_id = fields.Int(required=True)
    quantity = fields.Float(required=True)
    unit_price = fields.Float(allow_none=True)
    subtotal = fields.Float(allow_none=True)
    notes = fields.Str(allow_none=True)
    service_extra_type = fields.Nested(ServiceExtraTypeSchema, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
