from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models.laundry_delivery import LaundryDelivery
from models.laundry_service import LaundryService
from schemas.client_schema import ClientDetailSchema
from schemas.laundry_delivery_schema import LaundryDeliverySchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_schema import UserSchema

laundry_delivery_bp = Blueprint("laundry_delivery_bp", __name__, url_prefix="/laundry_deliveries")
schema = LaundryDeliverySchema()
schema_list = LaundryDeliverySchema(many=True)

transaction_schema = TransactionSchema()
user_schema = UserSchema()
client_schema = ClientDetailSchema()


@laundry_delivery_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    laundry_service_id = request.args.get("laundry_service_id", type=int)
    status = request.args.get("status")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    query = LaundryDelivery.query

    if laundry_service_id:
        query = query.filter(LaundryDelivery.laundry_service_id == laundry_service_id)
    if status:
        query = query.filter(LaundryDelivery.status == status)
    if from_date:
        query = query.filter(LaundryDelivery.scheduled_delivery_at >= from_date)
    if to_date:
        query = query.filter(LaundryDelivery.scheduled_delivery_at <= to_date)

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
    created_by = delivery.created_by_user
    assigned_to = delivery.assigned_to_user

    result = {
        "id": delivery.id,
        "scheduled_delivery_at": delivery.scheduled_delivery_at,
        "delivered_at": delivery.delivered_at,
        "status": delivery.status,
        "cancel_note": delivery.cancel_note,
        "created_at": delivery.created_at,
        "updated_at": delivery.updated_at,
        "service": {
            "id": service.id,
            "status": service.status,
            "service_label": service.service_label
        } if service else None,
        "client": client_schema.dump(client) if client else None,
        "transaction": transaction_schema.dump(transaction) if transaction else None,
        "created_by": user_schema.dump(created_by) if created_by else None,
        "assigned_to": user_schema.dump(assigned_to) if assigned_to else None
    }

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

    item = LaundryDelivery(
        laundry_service_id=data["laundry_service_id"],
        created_by_user_id=current_user_id,
        assigned_to_user_id=data.get("assigned_to_user_id"),
        scheduled_delivery_at=data["scheduled_delivery_at"],
        delivered_at=data.get("delivered_at"),
        status="PENDING",
        cancel_note=data.get("cancel_note")
    )
    db.session.add(item)
    db.session.commit()

    print(f"[AUDIT] LaundryDelivery {item.id} created by user {current_user_id}")
    return jsonify(schema.dump(item)), 201


@laundry_delivery_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update(item_id):
    item = LaundryDelivery.query.get_or_404(item_id)
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

    if "assigned_to_user_id" in data:
        item.assigned_to_user_id = data["assigned_to_user_id"]
    if "scheduled_delivery_at" in data:
        item.scheduled_delivery_at = data["scheduled_delivery_at"]
    if "delivered_at" in data:
        item.delivered_at = data["delivered_at"]
    if "cancel_note" in data:
        item.cancel_note = data["cancel_note"]

    db.session.commit()

    print(f"[AUDIT] LaundryDelivery {item.id} updated by user {current_user_id}")
    return jsonify(schema.dump(item)), 200


@laundry_delivery_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryDelivery.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    current_user_id = get_jwt_identity()
    print(f"[AUDIT] LaundryDelivery {item.id} deleted by user {current_user_id}")
    return jsonify({"message": f"LaundryDelivery {item_id} deleted"}), 200


@laundry_delivery_bp.route("/<int:item_id>/update_status", methods=["PATCH"])
@jwt_required()
def update_status(item_id):
    item = LaundryDelivery.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data or "status" not in json_data:
        return jsonify({"error": "Missing 'status' in request"}), 400

    valid_statuses = ["PENDING", "DELIVERED", "CANCELLED"]
    new_status = json_data["status"]

    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Valid options: {valid_statuses}"}), 400

    item.status = new_status
    if new_status == "DELIVERED":
        from datetime import datetime
        item.delivered_at = datetime.utcnow()

    db.session.commit()

    current_user_id = get_jwt_identity()
    print(f"[AUDIT] LaundryDelivery {item.id} status changed to {new_status} by user {current_user_id}")
    return jsonify(schema.dump(item)), 200
