import pytz
from datetime import timezone

LOCAL_TZ = pytz.timezone("America/El_Salvador")

def to_local(dt_utc):
    if dt_utc is None:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(LOCAL_TZ)
