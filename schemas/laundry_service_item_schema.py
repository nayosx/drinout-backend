from marshmallow import Schema, fields, validate
from schemas.base import LocalDateTimeMixin
from schemas.garment_type_v2_schema import GarmentTypeV2Schema


class LaundryServiceItemInputSchema(Schema):
    garment_type_id = fields.Int(required=True)
    quantity = fields.Float(required=True, validate=validate.Range(min=0.01))
    unit_type = fields.Str(
        required=True,
        validate=validate.OneOf(["UNIT", "PAIR"]),
    )
    unit_price = fields.Float(allow_none=True)
    notes = fields.Str(allow_none=True)


class LaundryServiceItemSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    garment_type_id = fields.Int(required=True)
    quantity = fields.Float(required=True)
    unit_type = fields.Str(required=True)
    unit_price = fields.Float(allow_none=True)
    subtotal = fields.Float(allow_none=True)
    notes = fields.Str(allow_none=True)
    garment_type = fields.Nested(GarmentTypeV2Schema, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
