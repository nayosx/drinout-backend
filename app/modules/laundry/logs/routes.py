from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models.laundry_service import LaundryService
from models.laundry_service_log import LaundryServiceLog
from schemas.laundry_service_log_schema import LaundryServiceLogSchema

laundry_service_log_bp = Blueprint("laundry_service_log_bp", __name__, url_prefix="/laundry_notes")

log_schema = LaundryServiceLogSchema()
log_schema_list = LaundryServiceLogSchema(many=True)

@laundry_service_log_bp.route("/<int:service_id>/notes", methods=["POST"])
@jwt_required()
def create_log_note(service_id):
    json_data = request.get_json()
    if not json_data or "detail" not in json_data or "status" not in json_data:
        return jsonify({"error": "Missing 'detail' or 'status' in request"}), 400

    LaundryService.query.get_or_404(service_id)
    current_user_id = get_jwt_identity()

    log = LaundryServiceLog(
        laundry_service_id=service_id,
        status=json_data["status"],
        detail=json_data["detail"],
        created_by_user_id=current_user_id
    )

    db.session.add(log)
    db.session.commit()

    return jsonify(log_schema.dump(log)), 201

@laundry_service_log_bp.route("/<int:service_id>/notes", methods=["GET"])
@jwt_required()
def get_log_notes(service_id):
    LaundryService.query.get_or_404(service_id)

    logs = LaundryServiceLog.query \
        .filter_by(laundry_service_id=service_id) \
        .order_by(LaundryServiceLog.created_at.desc()) \
        .all()

    return jsonify(log_schema_list.dump(logs)), 200

@laundry_service_log_bp.route("/notes/<int:log_id>", methods=["DELETE"])
@jwt_required()
def delete_log_note(log_id):
    log = LaundryServiceLog.query.get_or_404(log_id)
    current_user_id = get_jwt_identity()

    if log.created_by_user_id != current_user_id:
        return jsonify({"error": "Unauthorized: You can only delete your own notes"}), 403

    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": f"Note {log_id} deleted"}), 200
