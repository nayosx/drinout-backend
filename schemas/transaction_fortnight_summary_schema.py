from marshmallow import Schema, fields


class TransactionFortnightSummaryItemSchema(Schema):
    year = fields.Int(required=True)
    month = fields.Int(required=True)
    fortnight = fields.Int(required=True)
    label = fields.Str(required=True)
    bucket_start_date = fields.Str(required=True)
    bucket_end_date = fields.Str(required=True)
    in_total = fields.Decimal(as_string=True, required=True)
    out_total = fields.Decimal(as_string=True, required=True)


class TransactionFortnightSummarySchema(Schema):
    range = fields.Dict(keys=fields.Str(), values=fields.Str(), required=True)
    filters = fields.Dict(keys=fields.Str(), values=fields.Raw(allow_none=True), required=True)
    items = fields.List(fields.Nested(TransactionFortnightSummaryItemSchema), required=True)
