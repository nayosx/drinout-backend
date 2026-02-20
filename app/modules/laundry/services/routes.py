from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models.laundry_service import LaundryService
from models.laundry_activity_log import LaundryActivityLog
from models.client import Client, ClientAddress
from schemas.laundry_service_schema import LaundryServiceAllSchema, LaundryServiceDetailSchema, LaundryServiceLiteSchema, LaundryServiceSchema, LaundryServiceGetSchema, LaundryServiceCompactSchema
from sqlalchemy.orm import selectinload
from app.modules.laundry.queue.service import fetch_queue_items, reorder_pending_ids
from app.modules.laundry.queue.events import emit_queue_updated

laundry_service_bp = Blueprint("laundry_service_bp", __name__, url_prefix="/laundry_services")

schema = LaundryServiceSchema()
schema_get = LaundryServiceGetSchema()
schema_get_list = LaundryServiceGetSchema(many=True)

compact_schema_many = LaundryServiceCompactSchema(many=True)

def map_status_to_log_enum(status):
    return {
        "PENDING": "PENDIENTE",
        "IN_PROGRESS": "EN_PROCESO",
        "READY_FOR_DELIVERY": "LISTO_PARA_ENVIO",
        "DELIVERED": "COMPLETADO",
        "CANCELLED": "CANCELADO"
    }.get(status)

def _get_socketio():
    return current_app.extensions.get("socketio")


def _emit_queue_for_status_and_all(socketio, statuses):
    if not socketio:
        return

    status_list = []
    for status in statuses:
        if status:
            status_list.append(status)

    seen_statuses = set()
    unique_statuses = []
    for status in status_list:
        if status in seen_statuses:
            continue
        seen_statuses.add(status)
        unique_statuses.append(status)

    emit_queue_updated(
        socketio,
        statuses=None,
        include_global_room=True,
        include_client_room=False,
    )
    for status in unique_statuses:
        emit_queue_updated(
            socketio,
            statuses=[status],
            include_global_room=True,
            include_client_room=False,
        )


@laundry_service_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    client_id = request.args.get("client_id", type=int)
    status = request.args.get("status")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    query = LaundryService.query

    if client_id:
        query = query.filter(LaundryService.client_id == client_id)
    if status:
        query = query.filter(LaundryService.status == status)
    if from_date:
        query = query.filter(LaundryService.scheduled_pickup_at >= from_date)
    if to_date:
        query = query.filter(LaundryService.scheduled_pickup_at <= to_date)

    if status:
        query = query.order_by(LaundryService.scheduled_pickup_at.asc())
    else:
        query = query.order_by(LaundryService.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": schema_get_list.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    }), 200

@laundry_service_bp.route("/<int:service_id>", methods=["GET"])
@jwt_required()
def get_laundry_service(service_id):
    service = LaundryService.query.get_or_404(service_id)
    return jsonify(schema_get.dump(service)), 200

@laundry_service_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = schema.load(json_data)
    current_user_id = get_jwt_identity()

    client = Client.query.get(data["client_id"])
    if not client:
        return jsonify({"error": "Client not found"}), 404

    address = ClientAddress.query.get(data["client_address_id"])
    if not address or address.client_id != data["client_id"]:
        return jsonify({"error": "Address does not belong to client"}), 400

    item = LaundryService(
        client_id=data["client_id"],
        client_address_id=data["client_address_id"],
        scheduled_pickup_at=data["scheduled_pickup_at"],
        service_label=data["service_label"],
        status=data["status"],
        transaction_id=data.get("transaction_id"),
        created_by_user_id=current_user_id
    )
    db.session.add(item)
    db.session.commit()

    log = LaundryActivityLog(
        laundry_service_id=item.id,
        user_id=current_user_id,
        action="CREACION",
        new_status=map_status_to_log_enum(item.status),
        description="Creación del servicio de lavandería."
    )
    db.session.add(log)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[item.status])

    return jsonify(schema.dump(item)), 201

@laundry_service_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update(item_id):
    item = LaundryService.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = schema.load(json_data, partial=True)
    current_user_id = get_jwt_identity()

    old_status = item.status
    status_changed = False

    if "client_id" in data:
        client = Client.query.get(data["client_id"])
        if not client:
            return jsonify({"error": "Client not found"}), 404
        item.client_id = data["client_id"]

    if "client_address_id" in data:
        address = ClientAddress.query.get(data["client_address_id"])
        if not address or address.client_id != item.client_id:
            return jsonify({"error": "Address does not belong to client"}), 400
        item.client_address_id = data["client_address_id"]

    if "scheduled_pickup_at" in data:
        item.scheduled_pickup_at = data["scheduled_pickup_at"]
    if "service_label" in data:
        item.service_label = data["service_label"]
    if "status" in data:
        if item.status != data["status"]:
            item.status = data["status"]
            status_changed = True
    if "transaction_id" in data:
        item.transaction_id = data["transaction_id"]

    db.session.commit()

    if status_changed:
        log = LaundryActivityLog(
            laundry_service_id=item.id,
            user_id=current_user_id,
            action="ACTUALIZACION",
            previous_status=map_status_to_log_enum(old_status),
            new_status=map_status_to_log_enum(item.status),
            description="Actualización de estado del servicio."
        )
        db.session.add(log)
        db.session.commit()

    if status_changed:
        socketio = _get_socketio()
        _emit_queue_for_status_and_all(
            socketio,
            statuses=[old_status, item.status],
        )

    return jsonify(schema.dump(item)), 200

@laundry_service_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryService.query.get_or_404(item_id)
    old_status = item.status

    db.session.delete(item)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(
            socketio,
            statuses=[old_status],
        )

    return jsonify({"message": f"LaundryService {item_id} deleted"}), 200

@laundry_service_bp.route("/<int:item_id>/update_status", methods=["PATCH"])
@jwt_required()
def update_status(item_id):
    item = LaundryService.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data or "status" not in json_data:
        return jsonify({"error": "Missing 'status' in request"}), 400

    valid_statuses = ["PENDING", "STARTED", "IN_PROGRESS", "READY_FOR_DELIVERY", "DELIVERED", "CANCELLED"]
    new_status = json_data["status"]

    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Valid options: {valid_statuses}"}), 400

    current_user_id = get_jwt_identity()
    old_status = item.status

    item.status = new_status
    db.session.commit()

    log = LaundryActivityLog(
        laundry_service_id=item.id,
        user_id=current_user_id,
        action="CAMBIO_ESTADO",
        previous_status=map_status_to_log_enum(old_status),
        new_status=map_status_to_log_enum(new_status),
        description=f"Cambio de estado a {new_status}"
    )
    db.session.add(log)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(
            socketio,
            statuses=[old_status, new_status],
        )

    return jsonify(schema.dump(item)), 200

@laundry_service_bp.route("/<int:service_id>/notes", methods=["GET"])
@jwt_required()
def get_laundry_service_with_messages(service_id):
    service = LaundryService.query.get_or_404(service_id)
    return jsonify(LaundryServiceAllSchema().dump(service)), 200

@laundry_service_bp.route("/lite", methods=["GET"])
@jwt_required()
def get_lite():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    status = request.args.get("status")
    client_id = request.args.get("client_id", type=int)

    query = LaundryService.query

    if client_id:
        query = query.filter_by(client_id=client_id)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(LaundryService.scheduled_pickup_at.asc() if status else LaundryService.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    schema_lite = LaundryServiceLiteSchema(many=True)
    return jsonify({
        "items": schema_lite.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    }), 200

@laundry_service_bp.route("/detail", methods=["GET"])
@jwt_required()
def get_detail():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    status = request.args.get("status")
    client_id = request.args.get("client_id", type=int)

    query = LaundryService.query

    if client_id:
        query = query.filter_by(client_id=client_id)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(LaundryService.scheduled_pickup_at.asc() if status else LaundryService.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    schema_detail = LaundryServiceDetailSchema(many=True)
    return jsonify({
        "items": schema_detail.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    }), 200

@laundry_service_bp.route("/compact", methods=["GET"])
@jwt_required()
def get_compact():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    status = request.args.get("status")
    client_id = request.args.get("client_id", type=int)

    sort_mode = request.args.get("sort_mode")
    sort_by = request.args.get("sort_by")
    sort_dir = request.args.get("sort_dir", default="desc").lower()

    query = LaundryService.query.options(
        selectinload(LaundryService.client),
        selectinload(LaundryService.client_address),
        selectinload(LaundryService.created_by_user)
    )

    if client_id:
        query = query.filter_by(client_id=client_id)
    if status:
        query = query.filter_by(status=status)

    allowed_sort_by = {
        "id": LaundryService.id,
        "scheduled_pickup_at": LaundryService.scheduled_pickup_at,
        "created_at": LaundryService.created_at,
        "status": LaundryService.status,
        "service_label": LaundryService.service_label
    }

    def apply_default_order(q):
        if status:
            return q.order_by(LaundryService.scheduled_pickup_at.asc(), LaundryService.id.asc())
        return q.order_by(LaundryService.id.desc())

    def apply_mode(q, mode: str):
        mode = (mode or "").lower()
        if mode == "recent":
            return q.order_by(LaundryService.id.desc())
        if mode == "oldest":
            return q.order_by(LaundryService.id.asc())
        if mode == "agenda":
            return q.order_by(LaundryService.scheduled_pickup_at.asc(), LaundryService.id.asc())
        return apply_default_order(q)

    if sort_mode:
        query = apply_mode(query, sort_mode)
    elif sort_by in allowed_sort_by:
        col = allowed_sort_by[sort_by]
        if sort_dir == "asc":
            query = query.order_by(col.asc(), LaundryService.id.asc())
        else:
            query = query.order_by(col.desc(), LaundryService.id.desc())
    else:
        query = apply_default_order(query)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": compact_schema_many.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "sort_mode": sort_mode,
        "sort_by": sort_by,
        "sort_dir": sort_dir
    }), 200

@laundry_service_bp.route("/queue", methods=["GET"])
@jwt_required()
def get_queue():
    client_id = request.args.get("client_id", type=int)
    status_raw = request.args.get("status")

    items, err, code = fetch_queue_items(client_id, status_raw)
    if err:
        return jsonify(err), code

    return jsonify({
        "items": compact_schema_many.dump(items),
        "total": len(items)
    }), 200

@laundry_service_bp.route("/pending/reorder", methods=["PATCH"])
@jwt_required()
def reorder_pending():
    json_data = request.get_json()
    if not json_data or "ids" not in json_data:
        return jsonify({"error": "Missing 'ids' in request"}), 400

    current_user_id = get_jwt_identity()
    payload, code = reorder_pending_ids(json_data.get("ids"), current_user_id)

    if code == 200:
        socketio = _get_socketio()
        if socketio:
            _emit_queue_for_status_and_all(
                socketio,
                statuses=["PENDING"],
            )

    return jsonify(payload), code
