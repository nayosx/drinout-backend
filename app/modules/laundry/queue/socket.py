from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import join_room, leave_room
from services.laundry_queue_service import reorder_pending_ids, fetch_queue_items
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

def register_laundry_queue_socket(socketio):
    schema_many = LaundryServiceCompactSchema(many=True)

    @socketio.on("connect")
    def connect_handler(auth):
        token = None

        if isinstance(auth, dict):
            token = auth.get("token")

        if not token:
            token = request.args.get("token")

        if not token:
            return False

        try:
            decoded = decode_token(token)
            sub = decoded.get("sub")
            user_id = _safe_int(sub)
            if user_id is None:
                return False
            request.environ["laundry_user_id"] = user_id
        except Exception:
            return False

        return True

    @socketio.on("laundry:queue:join")
    def join_queue(data):
        try:
            client_id = None
            statuses_raw = None

            if isinstance(data, dict):
                client_id = data.get("client_id")
                statuses_raw = data.get("status")

            room = build_queue_room(client_id, statuses_raw)
            join_room(room)

            statuses_norm = _normalize_statuses(statuses_raw)
            items, err, err_code = fetch_queue_items(client_id, statuses_norm)

            if err:
                return {"ok": False, "error": err, "code": err_code, "room": room}

            return {
                "ok": True,
                "room": room,
                "filters": {"client_id": _safe_int(client_id), "status": statuses_norm},
                "items": schema_many.dump(items),
                "total": len(items)
            }
        except Exception as e:
            return {"ok": False, "error": {"error": str(e)}, "code": 500}

    @socketio.on("laundry:queue:leave")
    def leave_queue(data):
        try:
            client_id = None
            statuses_raw = None

            if isinstance(data, dict):
                client_id = data.get("client_id")
                statuses_raw = data.get("status")

            room = build_queue_room(client_id, statuses_raw)
            leave_room(room)

            return {"ok": True, "room": room}
        except Exception as e:
            return {"ok": False, "error": {"error": str(e)}, "code": 500}

    @socketio.on("laundry:pending:reorder")
    def pending_reorder(data):
        try:
            user_id = request.environ.get("laundry_user_id")
            if not user_id:
                return {"ok": False, "error": {"error": "Unauthorized"}, "code": 401}

            ids = None
            client_id = None
            statuses_raw = None

            if isinstance(data, dict):
                ids = data.get("ids")
                client_id = data.get("client_id")
                statuses_raw = data.get("status")

            if not isinstance(ids, list) or len(ids) == 0:
                return {"ok": False, "error": {"error": "ids must be a non-empty list"}, "code": 400}

            parsed_ids = []
            for x in ids:
                n = _safe_int(x)
                if n is not None:
                    parsed_ids.append(n)

            if len(parsed_ids) == 0:
                return {"ok": False, "error": {"error": "ids must contain at least one valid integer"}, "code": 400}

            payload, code = reorder_pending_ids(parsed_ids, user_id)
            if code != 200:
                return {"ok": False, "error": payload, "code": code}

            statuses_norm = _normalize_statuses(statuses_raw)
            room = build_queue_room(client_id, statuses_norm)

            items, err, err_code = fetch_queue_items(client_id, statuses_norm)
            if err:
                socketio.emit("laundry:queue:error", {"error": err, "code": err_code}, room=room)
                return {"ok": True, "result": payload, "room": room}

            socketio.emit(
                "laundry:queue:updated",
                {"items": schema_many.dump(items), "total": len(items), "filters": {"client_id": _safe_int(client_id), "status": statuses_norm}},
                room=room
            )

            return {"ok": True, "result": payload, "room": room}
        except Exception as e:
            return {"ok": False, "error": {"error": str(e)}, "code": 500}

    @socketio.on("laundry:queue:ping")
    def queue_ping(data):
        return {"ok": True, "echo": data}
