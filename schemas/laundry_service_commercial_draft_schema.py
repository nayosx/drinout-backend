from marshmallow import Schema, fields

from schemas.base import LocalDateTimeMixin


class LaundryServiceCommercialDraftCreateSchema(Schema):
    payload = fields.Raw(required=True)
    laundry_service_id = fields.Int(allow_none=True)
    is_confirmed = fields.Bool(load_default=False)
    confirmed_at = fields.DateTime(allow_none=True)
    charged_by_user_id = fields.Int(allow_none=True)


class LaundryServiceCommercialDraftPatchSchema(Schema):
    payload = fields.Raw(required=False)
    laundry_service_id = fields.Int(allow_none=True)
    is_confirmed = fields.Bool()
    confirmed_at = fields.DateTime(allow_none=True)
    charged_by_user_id = fields.Int(allow_none=True)


class LaundryServiceCommercialDraftSchema(LocalDateTimeMixin, Schema):
    id = fields.Int(dump_only=True)
    laundry_service_id = fields.Int(allow_none=True)
    client_id = fields.Int(allow_none=True, dump_only=True)
    client_address_id = fields.Int(allow_none=True, dump_only=True)
    transaction_id = fields.Int(allow_none=True, dump_only=True)
    payment_type_id = fields.Int(allow_none=True, dump_only=True)
    pricing_profile_id = fields.Int(allow_none=True, dump_only=True)
    status = fields.Str(allow_none=True, dump_only=True)
    service_label = fields.Str(allow_none=True, dump_only=True)
    scheduled_pickup_at = fields.DateTime(allow_none=True, dump_only=True)
    weight_lb = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    distance_km = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    delivery_price_per_km = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    delivery_fee_suggested = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    delivery_fee_final = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    delivery_fee_override_reason = fields.Str(allow_none=True, dump_only=True)
    global_discount_amount = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    global_discount_reason = fields.Str(allow_none=True, dump_only=True)
    quoted_service_amount = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    notes = fields.Str(allow_none=True, dump_only=True)
    payload = fields.Raw(dump_only=True)
    is_confirmed = fields.Bool()
    confirmed_at = fields.DateTime(allow_none=True)
    charged_by_user_id = fields.Int(allow_none=True)
    created_by_user_id = fields.Int(dump_only=True)
    updated_by_user_id = fields.Int(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

