BASE_ROOM = "laundry:queue"


def safe_int(value):
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        return int(value)
    except Exception:
        return None


def normalize_status_one(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s.upper()


def normalize_statuses(value):
    if value is None:
        return []

    statuses = []

    if isinstance(value, (list, tuple, set)):
        for x in value:
            s = normalize_status_one(x)
            if s:
                if s == "ALL":
                    return []
                statuses.append(s)
    else:
        raw = str(value).strip()
        if raw:
            if raw.upper() == "ALL":
                return []
            parts = [p.strip() for p in raw.split(",")]
            for p in parts:
                s = normalize_status_one(p)
                if s:
                    if s == "ALL":
                        return []
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
    statuses_norm = normalize_statuses(statuses_raw)

    if len(statuses_norm) > 0:
        status_key = "status:" + "+".join(statuses_norm)
    else:
        status_key = "status:all"

    return f"{BASE_ROOM}:{status_key}"
