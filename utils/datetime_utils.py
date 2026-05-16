import pytz
from datetime import timezone

_cached_tz = None
_fallback = "America/El_Salvador"


def _get_local_tz():
    global _cached_tz
    if _cached_tz is not None:
        return _cached_tz

    try:
        from models.global_setting import GlobalSetting
        setting = GlobalSetting.query.filter_by(key="timezone", is_active=True).first()
        tz_name = setting.value if setting else _fallback
    except Exception:
        tz_name = _fallback

    _cached_tz = pytz.timezone(tz_name)
    return _cached_tz


def to_local(dt_utc):
    if dt_utc is None:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(_get_local_tz())
