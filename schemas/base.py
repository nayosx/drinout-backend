from marshmallow import fields, post_dump
from utils.datetime_utils import to_local

class LocalDateTimeMixin:
    @post_dump
    def convert_datetimes(self, data, **kwargs):
        for k, v in data.items():
            if isinstance(v, str):
                try:
                    iso = fields.DateTime()._deserialize(v, None, None)
                    data[k] = to_local(iso).isoformat()
                except Exception:
                    pass
        return data
