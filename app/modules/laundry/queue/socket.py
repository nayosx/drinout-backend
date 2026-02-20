from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import join_room, leave_room
from app.modules.laundry.queue.common import build_queue_room, normalize_statuses, safe_int
from app.modules.laundry.queue.events import emit_queue_updated
from app.modules.laundry.queue.service import reorder_pending_ids, fetch_queue_items
from schemas.laundry_service_schema import LaundryServiceCompactSchema

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
            user_id = safe_int(sub)
            if user_id is None:
                return False
            request.environ["laundry_user_id"] = user_id
        except Exception:
            return False

        return True

    @socketio.on("laundry:queue:join")
    def join_queue(data):
        try:
            statuses_raw = None

            if isinstance(data, dict):
                statuses_raw = data.get("status")

            room = build_queue_room(None, statuses_raw)
            join_room(room)

            statuses_norm = normalize_statuses(statuses_raw)
            items, err, err_code = fetch_queue_items(None, statuses_norm)

            if err:
                return {"ok": False, "error": err, "code": err_code, "room": room}

            return {
                "ok": True,
                "room": room,
                "filters": {"status": statuses_norm},
                "items": schema_many.dump(items),
                "total": len(items)
            }
        except Exception as e:
            return {"ok": False, "error": {"error": str(e)}, "code": 500}

    @socketio.on("laundry:queue:leave")
    def leave_queue(data):
        try:
            statuses_raw = None

            if isinstance(data, dict):
                statuses_raw = data.get("status")

            room = build_queue_room(None, statuses_raw)
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
            statuses_raw = None

            if isinstance(data, dict):
                ids = data.get("ids")
                statuses_raw = data.get("status")

            if not isinstance(ids, list) or len(ids) == 0:
                return {"ok": False, "error": {"error": "ids must be a non-empty list"}, "code": 400}

            parsed_ids = []
            for x in ids:
                n = safe_int(x)
                if n is not None:
                    parsed_ids.append(n)

            if len(parsed_ids) == 0:
                return {"ok": False, "error": {"error": "ids must contain at least one valid integer"}, "code": 400}

            payload, code = reorder_pending_ids(parsed_ids, user_id)
            if code != 200:
                return {"ok": False, "error": payload, "code": code}

            emit_queue_updated(
                socketio,
                statuses=["PENDING"],
                include_global_room=True,
                include_client_room=False,
            )
            emit_queue_updated(
                socketio,
                statuses=None,
                include_global_room=True,
                include_client_room=False,
            )

            return {
                "ok": True,
                "result": payload,
                "room": build_queue_room(None, statuses_raw),
            }
        except Exception as e:
            return {"ok": False, "error": {"error": str(e)}, "code": 500}

    @socketio.on("laundry:queue:ping")
    def queue_ping(data):
        return {"ok": True, "echo": data}
