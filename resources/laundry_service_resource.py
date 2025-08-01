from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models.laundry_service import LaundryService
from models.laundry_activity_log import LaundryActivityLog
from models.client import Client, ClientAddress
from schemas.client_schema import ClientDetailSchema, ClientAddressNoUpdateSchema
from schemas.laundry_service_schema import LaundryServiceAllSchema, LaundryServiceDetailSchema, LaundryServiceLiteSchema, LaundryServiceSchema, LaundryServiceGetSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_schema import UserSchema

laundry_service_bp = Blueprint("laundry_service_bp", __name__, url_prefix="/laundry_services")

schema = LaundryServiceSchema()
schema_get = LaundryServiceGetSchema()
schema_get_list = LaundryServiceGetSchema(many=True)

def map_status_to_log_enum(status):
    return {
        "PENDING": "PENDIENTE",
        "IN_PROGRESS": "EN_PROCESO",
        "READY_FOR_DELIVERY": "LISTO_PARA_ENVIO",
        "DELIVERED": "COMPLETADO",
        "CANCELLED": "CANCELADO"
    }.get(status)


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
    previous_status = map_status_to_log_enum(item.status)
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
            previous_status=previous_status,
            new_status=map_status_to_log_enum(item.status),
            description="Actualización de estado del servicio."
        )
        db.session.add(log)
        db.session.commit()

    return jsonify(schema.dump(item)), 200


@laundry_service_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryService.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
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
    previous_status = map_status_to_log_enum(item.status)

    item.status = new_status
    db.session.commit()

    log = LaundryActivityLog(
        laundry_service_id=item.id,
        user_id=current_user_id,
        action="CAMBIO_ESTADO",
        previous_status=previous_status,
        new_status=map_status_to_log_enum(new_status),
        description=f"Cambio de estado a {new_status}"
    )
    db.session.add(log)
    db.session.commit()

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

    schema = LaundryServiceLiteSchema(many=True)
    return jsonify({
        "items": schema.dump(pagination.items),
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

    schema = LaundryServiceDetailSchema(many=True)
    return jsonify({
        "items": schema.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    }), 200
