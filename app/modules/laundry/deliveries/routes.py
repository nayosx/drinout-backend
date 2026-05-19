from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from datetime import datetime, timedelta
from models.laundry_delivery import LaundryDelivery
from models.laundry_service import LaundryService
from models.delivery_status_log import DeliveryStatusLog
from app.modules.laundry.queue.events import emit_queue_updated
from schemas.client_schema import ClientDetailSchema
from schemas.laundry_delivery_schema import LaundryDeliverySchema
from schemas.delivery_status_log_schema import DeliveryStatusLogSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_schema import UserSchema

laundry_delivery_bp = Blueprint("laundry_delivery_bp", __name__, url_prefix="/laundry_deliveries")
schema = LaundryDeliverySchema()
schema_list = LaundryDeliverySchema(many=True)
log_schema = DeliveryStatusLogSchema()
log_schema_list = DeliveryStatusLogSchema(many=True)

transaction_schema = TransactionSchema()
user_schema = UserSchema()
client_schema = ClientDetailSchema()


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


def _log_status_change(dispatch_id, status):
    log = DeliveryStatusLog(dispatch_id=dispatch_id, status=status)
    db.session.add(log)
    return log


@laundry_delivery_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    laundry_service_id = request.args.get("laundry_service_id", type=int)
    manager_id = request.args.get("manager_id", type=int)
    driver_id = request.args.get("driver_id", type=int)
    status = request.args.get("status")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    query = LaundryDelivery.query

    if laundry_service_id:
        query = query.filter(LaundryDelivery.laundry_service_id == laundry_service_id)
    if manager_id:
        query = query.filter(LaundryDelivery.manager_id == manager_id)
    if driver_id:
        query = query.filter(LaundryDelivery.driver_id == driver_id)
    if status:
        query = query.filter(LaundryDelivery.status == status)
    if from_date:
        query = query.filter(LaundryDelivery.scheduled_departure_time >= from_date)
    if to_date:
        to_date_parsed = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(LaundryDelivery.scheduled_departure_time < to_date_parsed)

    pagination = query.order_by(LaundryDelivery.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": schema_list.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    }), 200


@laundry_delivery_bp.route("/<int:delivery_id>", methods=["GET"])
@jwt_required()
def get_laundry_delivery(delivery_id):
    delivery = LaundryDelivery.query.get_or_404(delivery_id)
    service = delivery.laundry_service
    client = service.client if service else None
    transaction = service.transaction if service else None
    manager = delivery.manager
    driver = delivery.driver

    status_logs = DeliveryStatusLog.query.filter_by(dispatch_id=delivery.id).order_by(DeliveryStatusLog.logged_at.desc()).all()

    result = schema.dump(delivery)
    result["service"] = {
        "id": service.id,
        "status": service.status,
        "service_label": service.service_label
    } if service else None
    result["client"] = client_schema.dump(client) if client else None
    result["transaction"] = transaction_schema.dump(transaction) if transaction else None
    result["manager"] = user_schema.dump(manager) if manager else None
    result["driver"] = user_schema.dump(driver) if driver else None
    result["status_logs"] = log_schema_list.dump(status_logs)

    return jsonify(result), 200


@laundry_delivery_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = schema.load(json_data)
    current_user_id = get_jwt_identity()

    service = LaundryService.query.get(data["laundry_service_id"])
    if not service:
        return jsonify({"error": "LaundryService not found"}), 404

    if service.status not in ["PENDING", "READY_FOR_DELIVERY"]:
        return jsonify({
            "error": f"LaundryService must be PENDING or READY_FOR_DELIVERY to create a dispatch (current: {service.status})"
        }), 422

    manager_id = data.get("manager_id", current_user_id)

    # Idempotencia: si ya existe un dispatch activo para este servicio, retornarlo
    existing = LaundryDelivery.query.filter(
        LaundryDelivery.laundry_service_id == data["laundry_service_id"],
        LaundryDelivery.status.in_(["ASSIGNED", "EN_ROUTE"])
    ).first()

    if existing:
        if existing.scheduled_departure_time and existing.scheduled_departure_time.date() < datetime.utcnow().date():
            # Entrega antigua de fecha pasada — cerrarla automáticamente
            if existing.status == "EN_ROUTE":
                existing.status = "DELIVERED"
                existing.actual_delivery_time = datetime.utcnow()
                if service and service.status == "READY_FOR_DELIVERY":
                    service.status = "DELIVERED"
            else:
                existing.status = "REJECTED"
            existing.notes = "Close by system"
            _log_status_change(existing.id, existing.status)
            print(f"[AUDIT] LaundryDelivery {existing.id} auto-closed for service {data['laundry_service_id']}")
            # Continuar para crear la nueva entrega
        else:
            print(f"[AUDIT] LaundryDelivery {existing.id} returned as existing for service {data['laundry_service_id']}")
            return jsonify(schema.dump(existing)), 200

    item = LaundryDelivery(
        laundry_service_id=data["laundry_service_id"],
        manager_id=manager_id,
        driver_id=data["driver_id"],
        scheduled_departure_time=data["scheduled_departure_time"],
        customer_expected_time=data["customer_expected_time"],
        status="ASSIGNED"
    )
    db.session.add(item)
    db.session.flush()  # get item.id before commit

    _log_status_change(item.id, "ASSIGNED")
    db.session.commit()

    socketio = _get_socketio()
    if socketio and service:
        _emit_queue_for_status_and_all(socketio, statuses=[service.status])

    print(f"[AUDIT] LaundryDelivery {item.id} created by user {current_user_id}")
    return jsonify(schema.dump(item)), 201


@laundry_delivery_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update(item_id):
    item = LaundryDelivery.query.get_or_404(item_id)
    old_service = item.laundry_service
    old_service_status = old_service.status if old_service else None
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = schema.load(json_data, partial=True)
    current_user_id = get_jwt_identity()

    if "laundry_service_id" in data:
        service = LaundryService.query.get(data["laundry_service_id"])
        if not service:
            return jsonify({"error": "LaundryService not found"}), 404
        item.laundry_service_id = data["laundry_service_id"]

    if "driver_id" in data:
        item.driver_id = data["driver_id"]
    if "scheduled_departure_time" in data:
        item.scheduled_departure_time = data["scheduled_departure_time"]
    if "customer_expected_time" in data:
        item.customer_expected_time = data["customer_expected_time"]
    if "notes" in data:
        item.notes = data["notes"]

    db.session.commit()

    new_service = item.laundry_service
    new_service_status = new_service.status if new_service else None
    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[old_service_status, new_service_status])

    print(f"[AUDIT] LaundryDelivery {item.id} updated by user {current_user_id}")
    return jsonify(schema.dump(item)), 200


@laundry_delivery_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryDelivery.query.get_or_404(item_id)
    service = item.laundry_service
    service_status = service.status if service else None
    db.session.delete(item)
    db.session.commit()
    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[service_status])
    current_user_id = get_jwt_identity()
    print(f"[AUDIT] LaundryDelivery {item.id} deleted by user {current_user_id}")
    return jsonify({"message": f"LaundryDelivery {item_id} deleted"}), 200


@laundry_delivery_bp.route("/<int:item_id>/update_status", methods=["PATCH"])
@jwt_required()
def update_status(item_id):
    item = LaundryDelivery.query.get_or_404(item_id)
    service = item.laundry_service
    service_status = service.status if service else None
    json_data = request.get_json()
    if not json_data or "status" not in json_data:
        return jsonify({"error": "Missing 'status' in request"}), 400

    valid_statuses = ["ASSIGNED", "EN_ROUTE", "DELIVERED", "REJECTED"]
    new_status = json_data["status"]

    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Valid options: {valid_statuses}"}), 400

    # Notas opcional
    notes = json_data.get("notes")
    if notes is not None:
        item.notes = notes

    # Idempotencia: si ya está en el estado deseado con los efectos secundarios aplicados
    if new_status == item.status:
        if new_status == "EN_ROUTE" and item.actual_departure_time is not None:
            return jsonify(schema.dump(item)), 200
        if new_status == "DELIVERED" and item.actual_delivery_time is not None:
            return jsonify(schema.dump(item)), 200

    if new_status == "EN_ROUTE":
        # Solo una entrega activa por driver
        existing_active = LaundryDelivery.query.filter(
            LaundryDelivery.driver_id == item.driver_id,
            LaundryDelivery.status == "EN_ROUTE",
            LaundryDelivery.id != item.id
        ).first()

        if existing_active:
            return jsonify({
                "error": f"El repartidor ya tiene una entrega en curso (dispatch #{existing_active.id}). Debe completarla o rechazarla primero."
            }), 409

        item.actual_departure_time = datetime.utcnow()
    elif new_status == "DELIVERED":
        item.actual_delivery_time = datetime.utcnow()
        if service and service.status == "READY_FOR_DELIVERY":
            service.status = "DELIVERED"
    elif new_status == "REJECTED":
        pass

    item.status = new_status
    _log_status_change(item.id, new_status)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[service_status])
        if service:
            _emit_queue_for_status_and_all(socketio, statuses=[service.status])

    current_user_id = get_jwt_identity()
    print(f"[AUDIT] LaundryDelivery {item.id} status changed to {new_status} by user {current_user_id}")
    return jsonify(schema.dump(item)), 200


@laundry_delivery_bp.route("/<int:dispatch_id>/status-logs", methods=["GET"])
@jwt_required()
def get_status_logs(dispatch_id):
    logs = DeliveryStatusLog.query.filter_by(dispatch_id=dispatch_id).order_by(DeliveryStatusLog.logged_at.desc()).all()
    return jsonify({"items": log_schema_list.dump(logs)}), 200


@laundry_delivery_bp.route("/metrics", methods=["GET"])
@jwt_required()
def get_metrics():
    driver_id = request.args.get("driver_id", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    query = LaundryDelivery.query.filter(LaundryDelivery.status == "DELIVERED")

    if driver_id:
        query = query.filter(LaundryDelivery.driver_id == driver_id)
    if date_from:
        query = query.filter(LaundryDelivery.actual_delivery_time >= date_from)
    if date_to:
        date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(LaundryDelivery.actual_delivery_time < date_to_parsed)

    results = query.order_by(LaundryDelivery.actual_delivery_time.desc()).all()

    metrics = []
    for d in results:
        service = d.laundry_service
        client = service.client if service else None
        metrics.append({
            "dispatch_id": d.id,
            "laundry_service_id": d.laundry_service_id,
            "client_name": client.name if client else None,
            "driver_reaction_minutes": (
                (d.actual_departure_time - d.scheduled_departure_time).total_seconds() / 60
                if d.actual_departure_time and d.scheduled_departure_time else None
            ),
            "customer_delay_minutes": (
                (d.actual_delivery_time - d.customer_expected_time).total_seconds() / 60
                if d.actual_delivery_time and d.customer_expected_time else None
            ),
            "time_on_road_minutes": (
                (d.actual_delivery_time - d.actual_departure_time).total_seconds() / 60
                if d.actual_delivery_time and d.actual_departure_time else None
            )
        })

    return jsonify({"items": metrics}), 200
