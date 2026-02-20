from app.modules.laundry.queue.service import fetch_queue_items
from schemas.laundry_service_schema import LaundryServiceCompactSchema

BASE_ROOM = "laundry:queue"

def _safe_int(value):
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        return int(value)
    except Exception:
        return None

def _normalize_status_one(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s.upper()

def _normalize_statuses(value):
    if value is None:
        return []

    statuses = []

    if isinstance(value, (list, tuple, set)):
        for x in value:
            s = _normalize_status_one(x)
            if s:
                statuses.append(s)
    else:
        raw = str(value).strip()
        if raw:
            parts = [p.strip() for p in raw.split(",")]
            for p in parts:
                s = _normalize_status_one(p)
                if s:
                    statuses.append(s)

    uniq = []
    seen = set()
    for s in statuses:
        if s not in seen:
            seen.add(s)
            uniq.append(s)

    uniq.sort()
    return uniq

def build_queue_room(client_id, statuses_raw):
    client_int = _safe_int(client_id)
    statuses_norm = _normalize_statuses(statuses_raw)

    if client_int is not None:
        client_key = f"client:{client_int}"
    else:
        client_key = "client:all"

    if len(statuses_norm) > 0:
        status_key = "status:" + "+".join(statuses_norm)
    else:
        status_key = "status:all"

    return f"{BASE_ROOM}:{client_key}:{status_key}"

def emit_queue_updated(socketio, statuses=None, client_id=None, include_client_room=True):
    schema_many = LaundryServiceCompactSchema(many=True)
    statuses_norm = _normalize_statuses(statuses)

    targets = []
    targets.append((None, build_queue_room(None, statuses_norm)))

    if include_client_room and _safe_int(client_id) is not None:
        targets.append((_safe_int(client_id), build_queue_room(client_id, statuses_norm)))

    for target_client_id, room in targets:
        items, err, err_code = fetch_queue_items(target_client_id, statuses_norm)

        if err:
            socketio.emit("laundry:queue:error", {"error": err, "code": err_code}, room=room)
            continue

        socketio.emit(
            "laundry:queue:updated",
            {
                "items": schema_many.dump(items),
                "total": len(items),
                "filters": {"client_id": target_client_id, "status": statuses_norm}
            },
            room=room
        )
