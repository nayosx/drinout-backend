from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.payment_type import PaymentType
from schemas.payment_type_schema import PaymentTypeSchema

payment_type_bp = Blueprint("payment_type_bp", __name__, url_prefix="/payment_types")

payment_type_schema = PaymentTypeSchema()
payment_type_list_schema = PaymentTypeSchema(many=True)

@payment_type_bp.route("", methods=["GET"])
@jwt_required()
def get_all_payment_types():
    ptypes = PaymentType.query.all()
    return jsonify(payment_type_list_schema.dump(ptypes)), 200

@payment_type_bp.route("/<int:payment_type_id>", methods=["GET"])
@jwt_required()
def get_payment_type(payment_type_id):
    ptype = PaymentType.query.get_or_404(payment_type_id)
    return jsonify(payment_type_schema.dump(ptype)), 200

@payment_type_bp.route("", methods=["POST"])
@jwt_required()
def create_payment_type():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = payment_type_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    new_ptype = PaymentType(
        name=data["name"],
        description=data["description"]
    )
    db.session.add(new_ptype)
    db.session.commit()
    return jsonify({
        "message": "Payment type created",
        "payment_type": payment_type_schema.dump(new_ptype)
    }), 201

@payment_type_bp.route("/<int:payment_type_id>", methods=["PUT"])
@jwt_required()
def update_payment_type(payment_type_id):
    ptype = PaymentType.query.get_or_404(payment_type_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = payment_type_schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    if "name" in data:
        ptype.name = data["name"]
    if "description" in data:
        ptype.description = data["description"]
    db.session.commit()
    return jsonify({
        "message": "Payment type updated",
        "payment_type": payment_type_schema.dump(ptype)
    }), 200

@payment_type_bp.route("/<int:payment_type_id>", methods=["DELETE"])
@jwt_required()
def delete_payment_type(payment_type_id):
    ptype = PaymentType.query.get_or_404(payment_type_id)
    db.session.delete(ptype)
    db.session.commit()
    return jsonify({"message": f"Payment type {payment_type_id} deleted"}), 200
