from sqlalchemy.orm import selectinload
from sqlalchemy import case
from db import db
from models.laundry_service import LaundryService
from models.laundry_activity_log import LaundryActivityLog

allowed_statuses = {"PENDING", "STARTED", "IN_PROGRESS", "READY_FOR_DELIVERY", "DELIVERED", "CANCELLED"}

def _normalize_status_one(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s.upper()

def _normalize_statuses(status_raw):
    if status_raw is None:
        return []

    statuses = []

    if isinstance(status_raw, (list, tuple, set)):
        for x in status_raw:
            s = _normalize_status_one(x)
            if s:
                statuses.append(s)
    else:
        raw = str(status_raw).strip()
        if raw:
            if raw.upper() == "ALL":
                return []
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

def build_queue_query(client_id: int | None, status_raw):
    query = LaundryService.query.options(
        selectinload(LaundryService.client),
        selectinload(LaundryService.client_address),
        selectinload(LaundryService.created_by_user)
    )

    if client_id:
        query = query.filter(LaundryService.client_id == client_id)

    statuses = _normalize_statuses(status_raw)

    if len(statuses) > 0:
        invalid = [s for s in statuses if s not in allowed_statuses]
        if invalid:
            return None, {"error": "Invalid status", "invalid": invalid, "valid": sorted(list(allowed_statuses))}, 400

        query = query.filter(LaundryService.status.in_(statuses))

    if statuses == ["PENDING"]:
        query = query.order_by(LaundryService.pending_order.asc(), LaundryService.id.asc())
    else:
        pending_first = case((LaundryService.status == "PENDING", 0), else_=1)
        pending_order_safe = case((LaundryService.status == "PENDING", LaundryService.pending_order), else_=None)

        query = query.order_by(
            pending_first.asc(),
            pending_order_safe.asc(),
            LaundryService.scheduled_pickup_at.asc(),
            LaundryService.id.asc()
        )

    return query, None, 200

def fetch_queue_items(client_id: int | None, status_raw):
    query, err, code = build_queue_query(client_id, status_raw)
    if err:
        return None, err, code
    items = query.all()
    return items, None, 200

def reorder_pending_ids(ids, current_user_id: int):
    if not isinstance(ids, list) or len(ids) == 0:
        return {"error": "'ids' must be a non-empty list"}, 400

    try:
        ids_int = [int(x) for x in ids]
    except (TypeError, ValueError):
        return {"error": "'ids' must contain only integers"}, 400

    if len(set(ids_int)) != len(ids_int):
        return {"error": "Duplicate ids are not allowed"}, 400

    items = LaundryService.query.filter(LaundryService.id.in_(ids_int)).all()
    if len(items) != len(ids_int):
        found = {i.id for i in items}
        missing = [i for i in ids_int if i not in found]
        return {"error": "Some ids were not found", "missing": missing}, 404

    not_pending = [i.id for i in items if i.status != "PENDING"]
    if not_pending:
        return {"error": "All items must be PENDING to reorder", "not_pending": not_pending}, 400

    id_to_item = {i.id: i for i in items}

    for service_id in ids_int:
        id_to_item[service_id].pending_order = None

    db.session.flush()

    for idx, service_id in enumerate(ids_int, start=1):
        id_to_item[service_id].pending_order = idx

    log = LaundryActivityLog(
        laundry_service_id=ids_int[0],
        user_id=current_user_id,
        action="ACTUALIZACION",
        description=f"Reordenamiento manual de cola PENDING. Total items={len(ids_int)}"
    )
    db.session.add(log)

    db.session.commit()

    return {
        "message": "PENDING order updated",
        "count": len(ids_int),
        "ids": ids_int,
    }, 200
