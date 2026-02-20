from app.modules.laundry.queue.common import build_queue_room, normalize_statuses
from app.modules.laundry.queue.service import fetch_queue_items
from schemas.laundry_service_schema import LaundryServiceCompactSchema

def emit_queue_updated(
    socketio,
    statuses=None,
    client_id=None,
    include_client_room=True,
    include_global_room=True,
):
    schema_many = LaundryServiceCompactSchema(many=True)
    statuses_norm = normalize_statuses(statuses)

    if not include_global_room:
        return

    room = build_queue_room(None, statuses_norm)
    items, err, err_code = fetch_queue_items(None, statuses_norm)

    if err:
        socketio.emit("laundry:queue:error", {"error": err, "code": err_code}, room=room)
        return

    socketio.emit(
        "laundry:queue:updated",
        {
            "items": schema_many.dump(items),
            "total": len(items),
            "filters": {"status": statuses_norm}
        },
        room=room
    )
