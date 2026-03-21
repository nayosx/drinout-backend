from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.modules.laundry.queue.events import emit_queue_updated
from db import db
from models.client import Client, ClientAddress
from models.garment_type import GarmentType
from models.laundry_activity_log import LaundryActivityLog
from models.laundry_service import LaundryService
from models.laundry_service_extra import LaundryServiceExtra
from models.laundry_service_item import LaundryServiceItem
from models.service_extra_type import ServiceExtraType
from schemas.laundry_service_v2_schema import LaundryServiceV2Schema, LaundryServiceV2UpsertSchema


laundry_service_v2_bp = Blueprint("laundry_service_v2_bp", __name__, url_prefix="/v2/laundry_services")

schema = LaundryServiceV2Schema()
schema_many = LaundryServiceV2Schema(many=True)
upsert_schema = LaundryServiceV2UpsertSchema()


def map_status_to_log_enum(status):
    return {
        "PENDING": "PENDIENTE",
        "IN_PROGRESS": "EN_PROCESO",
        "READY_FOR_DELIVERY": "LISTO_PARA_ENVIO",
        "DELIVERED": "COMPLETADO",
        "CANCELLED": "CANCELADO",
    }.get(status)


def _get_socketio():
    return current_app.extensions.get("socketio")


def _sync_pending_order_for_status(item):
    if item.status != "PENDING":
        item.pending_order = None


def _next_pending_order():
    current_max = db.session.query(func.max(LaundryService.pending_order)).filter(
        LaundryService.status == "PENDING"
    ).scalar()
    return (current_max or 0) + 1


def _emit_queue_for_status_and_all(socketio, statuses):
    if not socketio:
        return

    unique_statuses = []
    seen_statuses = set()
    for status in statuses:
        if not status or status in seen_statuses:
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


def _as_money(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    else:
        decimal_value = Decimal(str(value))
    return decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _line_subtotal(quantity, unit_price):
    if unit_price is None:
        return None
    return _as_money(Decimal(str(quantity)) * Decimal(str(unit_price)))


def _validate_client_and_address(client_id, client_address_id):
    client = Client.query.get(client_id)
    if not client:
        return None, None, ({"error": "Client not found"}, 404)

    address = ClientAddress.query.get(client_address_id)
    if not address or address.client_id != client_id:
        return None, None, ({"error": "Address does not belong to client"}, 400)

    return client, address, None


def _build_item_models(items_data):
    models = []
    for row in items_data:
        garment_type = GarmentType.query.get(row["garment_type_id"])
        if not garment_type:
            return None, ({"error": f"GarmentType {row['garment_type_id']} not found"}, 404)

        unit_price = row.get("unit_price")
        subtotal = _line_subtotal(row["quantity"], unit_price)
        models.append(
            LaundryServiceItem(
                garment_type_id=row["garment_type_id"],
                quantity=_as_money(row["quantity"]),
                unit_type=row["unit_type"],
                unit_price=_as_money(unit_price),
                subtotal=subtotal,
                notes=row.get("notes"),
            )
        )
    return models, None


def _build_extra_models(extras_data):
    models = []
    for row in extras_data:
        extra_type = ServiceExtraType.query.get(row["service_extra_type_id"])
        if not extra_type:
            return None, ({"error": f"ServiceExtraType {row['service_extra_type_id']} not found"}, 404)

        unit_price = row.get("unit_price")
        subtotal = _line_subtotal(row["quantity"], unit_price)
        models.append(
            LaundryServiceExtra(
                service_extra_type_id=row["service_extra_type_id"],
                quantity=_as_money(row["quantity"]),
                unit_price=_as_money(unit_price),
                subtotal=subtotal,
                notes=row.get("notes"),
            )
        )
    return models, None


def _apply_nested_rows(service, data):
    if "items" in data:
        item_models, item_error = _build_item_models(data["items"])
        if item_error:
            return item_error
        service.items = item_models

    if "extras" in data:
        extra_models, extra_error = _build_extra_models(data["extras"])
        if extra_error:
            return extra_error
        service.extras = extra_models

    return None


def _service_query():
    return LaundryService.query.options(
        selectinload(LaundryService.client),
        selectinload(LaundryService.client_address),
        selectinload(LaundryService.transaction),
        selectinload(LaundryService.created_by_user),
        selectinload(LaundryService.logs),
        selectinload(LaundryService.items).selectinload(LaundryServiceItem.garment_type),
        selectinload(LaundryService.extras).selectinload(LaundryServiceExtra.service_extra_type),
    )


@laundry_service_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    client_id = request.args.get("client_id", type=int)
    status = request.args.get("status")

    query = _service_query()
    if client_id:
        query = query.filter(LaundryService.client_id == client_id)
    if status:
        query = query.filter(LaundryService.status == status)

    query = query.order_by(LaundryService.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": schema_many.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@laundry_service_v2_bp.route("/<int:service_id>", methods=["GET"])
@jwt_required()
def get_one(service_id):
    service = _service_query().filter(LaundryService.id == service_id).first_or_404()
    return jsonify(schema.dump(service)), 200


@laundry_service_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = upsert_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    _, _, validation_error = _validate_client_and_address(data["client_id"], data["client_address_id"])
    if validation_error:
        payload, code = validation_error
        return jsonify(payload), code

    current_user_id = get_jwt_identity()
    service = LaundryService(
        client_id=data["client_id"],
        client_address_id=data["client_address_id"],
        scheduled_pickup_at=data["scheduled_pickup_at"],
        service_label=data["service_label"],
        status=data["status"],
        transaction_id=data.get("transaction_id"),
        weight_lb=_as_money(data.get("weight_lb")),
        notes=data.get("notes"),
        created_by_user_id=current_user_id,
    )
    if service.status == "PENDING":
        service.pending_order = _next_pending_order()
    else:
        _sync_pending_order_for_status(service)

    nested_error = _apply_nested_rows(service, data)
    if nested_error:
        payload, code = nested_error
        return jsonify(payload), code

    db.session.add(service)
    db.session.commit()

    log = LaundryActivityLog(
        laundry_service_id=service.id,
        user_id=current_user_id,
        action="CREACION",
        new_status=map_status_to_log_enum(service.status),
        description="Creacion del servicio de lavanderia V2.",
    )
    db.session.add(log)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[service.status])

    service = _service_query().filter(LaundryService.id == service.id).first_or_404()
    return jsonify(schema.dump(service)), 201


@laundry_service_v2_bp.route("/<int:service_id>", methods=["PUT"])
@jwt_required()
def update(service_id):
    service = _service_query().filter(LaundryService.id == service_id).first_or_404()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = upsert_schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    current_user_id = get_jwt_identity()
    old_status = service.status

    next_client_id = data.get("client_id", service.client_id)
    next_address_id = data.get("client_address_id", service.client_address_id)
    _, _, validation_error = _validate_client_and_address(next_client_id, next_address_id)
    if validation_error:
        payload, code = validation_error
        return jsonify(payload), code

    if "client_id" in data:
        service.client_id = data["client_id"]
    if "client_address_id" in data:
        service.client_address_id = data["client_address_id"]
    if "scheduled_pickup_at" in data:
        service.scheduled_pickup_at = data["scheduled_pickup_at"]
    if "service_label" in data:
        service.service_label = data["service_label"]
    if "status" in data:
        service.status = data["status"]
    if "transaction_id" in data:
        service.transaction_id = data["transaction_id"]
    if "weight_lb" in data:
        service.weight_lb = _as_money(data["weight_lb"])
    if "notes" in data:
        service.notes = data["notes"]

    if old_status != "PENDING" and service.status == "PENDING":
        service.pending_order = _next_pending_order()
    else:
        _sync_pending_order_for_status(service)

    nested_error = _apply_nested_rows(service, data)
    if nested_error:
        payload, code = nested_error
        return jsonify(payload), code

    db.session.commit()

    if old_status != service.status:
        log = LaundryActivityLog(
            laundry_service_id=service.id,
            user_id=current_user_id,
            action="ACTUALIZACION",
            previous_status=map_status_to_log_enum(old_status),
            new_status=map_status_to_log_enum(service.status),
            description="Actualizacion del servicio de lavanderia V2.",
        )
        db.session.add(log)
        db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[old_status, service.status])

    service = _service_query().filter(LaundryService.id == service.id).first_or_404()
    return jsonify(schema.dump(service)), 200


@laundry_service_v2_bp.route("/<int:service_id>", methods=["DELETE"])
@jwt_required()
def delete(service_id):
    service = LaundryService.query.get_or_404(service_id)
    old_status = service.status
    db.session.delete(service)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[old_status])

    return jsonify({"message": f"LaundryService {service_id} deleted"}), 200
