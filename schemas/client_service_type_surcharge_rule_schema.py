from marshmallow import Schema, fields, validate

from schemas.base import LocalDateTimeMixin


class ClientServiceTypeSurchargeRuleSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int(required=True)
    service_label = fields.Str(
        required=True,
        validate=validate.OneOf(["NORMAL", "EXPRESS"]),
    )
    amount = fields.Decimal(
        required=True,
        as_string=True,
        validate=validate.Range(min=0),
    )
    is_active = fields.Bool(load_default=True)
    notes = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
