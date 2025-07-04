from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.client import ClientPhone
from schemas.client import ClientPhoneSchema

phones_bp = Blueprint("phones_bp", __name__, url_prefix="/client-phones")

phone_schema = ClientPhoneSchema()
phone_list_schema = ClientPhoneSchema(many=True)

@phones_bp.route("", methods=["GET"])
@jwt_required()
def get_phones():
    phones = ClientPhone.query.order_by(ClientPhone.id).all()
    return jsonify(phone_list_schema.dump(phones)), 200

@phones_bp.route("/<int:phone_id>", methods=["GET"])
@jwt_required()
def get_phone(phone_id):
    phone = ClientPhone.query.get_or_404(phone_id)
    return jsonify(phone_schema.dump(phone)), 200

@phones_bp.route("", methods=["POST"])
@jwt_required()
def create_phone():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = phone_schema.load(json_data)
    
    # Validar existencia del cliente
    from models.client import Client
    client = Client.query.get(data["client_id"])
    if client is None or client.is_deleted:
        return jsonify({"error": "Client not found"}), 404

    phone = ClientPhone(
        client_id=data["client_id"],
        phone_number=data["phone_number"],
        description=data.get("description"),
        is_primary=data.get("is_primary", False)
    )
    db.session.add(phone)
    db.session.commit()
    return jsonify(phone_schema.dump(phone)), 201


@phones_bp.route("/<int:phone_id>", methods=["PUT"])
@jwt_required()
def update_phone(phone_id):
    phone = ClientPhone.query.get_or_404(phone_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = phone_schema.load(json_data, partial=True)
    if "phone_number" in data:
        phone.phone_number = data["phone_number"]
    if "description" in data:
        phone.description = data["description"]
    if "is_primary" in data:
        phone.is_primary = data["is_primary"]
    db.session.commit()
    return jsonify(phone_schema.dump(phone)), 200

@phones_bp.route("/<int:phone_id>", methods=["DELETE"])
@jwt_required()
def delete_phone(phone_id):
    phone = ClientPhone.query.get_or_404(phone_id)
    db.session.delete(phone)
    db.session.commit()
    return jsonify({"message": f"Phone {phone_id} deleted"}), 200
