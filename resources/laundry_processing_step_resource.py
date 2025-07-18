from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models.laundry_processing_step import LaundryProcessingStep
from models.laundry_service import LaundryService
from schemas.laundry_processing_step_schema import LaundryProcessingStepSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_schema import UserSchema
from schemas.client_schema import ClientDetailSchema

processing_step_bp = Blueprint("processing_step_bp", __name__, url_prefix="/processing_steps")

schema = LaundryProcessingStepSchema()
schema_list = LaundryProcessingStepSchema(many=True)
transaction_schema = TransactionSchema()
user_schema = UserSchema()
client_schema = ClientDetailSchema()

@processing_step_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    laundry_service_id = request.args.get("laundry_service_id", type=int)
    step_type = request.args.get("step_type")

    query = LaundryProcessingStep.query

    if laundry_service_id:
        query = query.filter(LaundryProcessingStep.laundry_service_id == laundry_service_id)
    if step_type:
        query = query.filter(LaundryProcessingStep.step_type == step_type)

    pagination = query.order_by(LaundryProcessingStep.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": schema_list.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    }), 200


@processing_step_bp.route("/<int:step_id>", methods=["GET"])
@jwt_required()
def get_one(step_id):
    step = LaundryProcessingStep.query.get_or_404(step_id)
    service = step.laundry_service
    client = service.client if service else None
    transaction = service.transaction if service else None
    started_by = step.started_by_user
    completed_by = step.completed_by_user

    result = {
        "id": step.id,
        "step_type": step.step_type,
        "started_at": step.started_at,
        "completed_at": step.completed_at,
        "notes": step.notes,
        "service": {
            "id": service.id,
            "status": service.status,
            "service_label": service.service_label
        } if service else None,
        "client": client_schema.dump(client) if client else None,
        "transaction": transaction_schema.dump(transaction) if transaction else None,
        "started_by": user_schema.dump(started_by) if started_by else None,
        "completed_by": user_schema.dump(completed_by) if completed_by else None
    }

    return jsonify(result), 200


@processing_step_bp.route("", methods=["POST"])
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

    step = LaundryProcessingStep(
        laundry_service_id=data["laundry_service_id"],
        step_type=data.get("step_type", "LAVADO"),
        started_by_user_id=current_user_id,
        notes=data.get("notes")
    )
    db.session.add(step)
    db.session.commit()

    return jsonify(schema.dump(step)), 201


@processing_step_bp.route("/<int:step_id>", methods=["PUT"])
@jwt_required()
def update(step_id):
    step = LaundryProcessingStep.query.get_or_404(step_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = schema.load(json_data, partial=True)

    if "step_type" in data:
        step.step_type = data["step_type"]
    if "notes" in data:
        step.notes = data["notes"]

    db.session.commit()
    return jsonify(schema.dump(step)), 200


@processing_step_bp.route("/<int:step_id>", methods=["DELETE"])
@jwt_required()
def delete(step_id):
    step = LaundryProcessingStep.query.get_or_404(step_id)
    db.session.delete(step)
    db.session.commit()
    return jsonify({"message": f"LaundryProcessingStep {step_id} deleted"}), 200


@processing_step_bp.route("/<int:step_id>/complete", methods=["PATCH"])
@jwt_required()
def complete(step_id):
    step = LaundryProcessingStep.query.get_or_404(step_id)
    current_user_id = get_jwt_identity()

    from datetime import datetime
    step.completed_by_user_id = current_user_id
    step.completed_at = datetime.utcnow()

    db.session.commit()
    return jsonify(schema.dump(step)), 200
