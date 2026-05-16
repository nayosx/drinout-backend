import os
import pytz
from datetime import timezone

TIMEZONE = os.getenv("TIMEZONE", "America/El_Salvador")
LOCAL_TZ = pytz.timezone(TIMEZONE)


def to_local(dt_utc):
    if dt_utc is None:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(LOCAL_TZ)


def localize_naive(naive_dt, is_dst=False):
    """Convierte un datetime naive a timezone-aware usando la TZ configurada."""
    return LOCAL_TZ.localize(naive_dt, is_dst)
