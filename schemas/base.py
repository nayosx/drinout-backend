from marshmallow import Schema, fields, post_dump, pre_load
from utils.datetime_utils import to_local, localize_naive
from datetime import datetime, timezone

class LocalDateTimeMixin:
    @pre_load
    def normalize_input_datetimes(self, data, **kwargs):
        """Convierte fechas entrantes (naive o aware) a UTC naive antes de almacenar."""
        if not isinstance(data, dict):
            return data
        for key, value in data.items():
            if not isinstance(value, str):
                continue
            try:
                dt = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                continue
            if dt.tzinfo is not None:
                dt_utc = dt.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                dt_utc = localize_naive(dt).astimezone(timezone.utc).replace(tzinfo=None)
            data[key] = dt_utc.isoformat()
        return data

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


class BaseSchema(LocalDateTimeMixin, Schema):
    """Schema base con manejo automatico de timezone.

    @pre_load: normaliza fechas entrantes a UTC naive (naive = hora local).
    @post_dump: convierte UTC -> hora local en serializacion.
    Timezone configurable via .env TIMEZONE.
    """
    pass
