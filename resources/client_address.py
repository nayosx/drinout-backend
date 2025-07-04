from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.client import ClientAddress
from schemas.client import ClientAddressSchema

addresses_bp = Blueprint("addresses_bp", __name__, url_prefix="/client-addresses")

address_schema = ClientAddressSchema()
address_list_schema = ClientAddressSchema(many=True)

@addresses_bp.route("", methods=["GET"])
@jwt_required()
def get_addresses():
    addresses = ClientAddress.query.order_by(ClientAddress.id).all()
    return jsonify(address_list_schema.dump(addresses)), 200

@addresses_bp.route("/<int:address_id>", methods=["GET"])
@jwt_required()
def get_address(address_id):
    address = ClientAddress.query.get_or_404(address_id)
    return jsonify(address_schema.dump(address)), 200

@addresses_bp.route("", methods=["POST"])
@jwt_required()
def create_address():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = address_schema.load(json_data)
    
    # Validar existencia del cliente
    from models.client import Client
    client = Client.query.get(data["client_id"])
    if client is None or client.is_deleted:
        return jsonify({"error": "Client not found"}), 404

    address = ClientAddress(
        client_id=data["client_id"],
        address_text=data["address_text"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        map_link=data.get("map_link"),
        image_path=data.get("image_path"),
        is_primary=data.get("is_primary", False)
    )
    db.session.add(address)
    db.session.commit()
    return jsonify(address_schema.dump(address)), 201


@addresses_bp.route("/<int:address_id>", methods=["PUT"])
@jwt_required()
def update_address(address_id):
    address = ClientAddress.query.get_or_404(address_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = address_schema.load(json_data, partial=True)
    if "address_text" in data:
        address.address_text = data["address_text"]
    if "latitude" in data:
        address.latitude = data["latitude"]
    if "longitude" in data:
        address.longitude = data["longitude"]
    if "map_link" in data:
        address.map_link = data["map_link"]
    if "image_path" in data:
        address.image_path = data["image_path"]
    if "is_primary" in data:
        address.is_primary = data["is_primary"]
    db.session.commit()
    return jsonify(address_schema.dump(address)), 200

@addresses_bp.route("/<int:address_id>", methods=["DELETE"])
@jwt_required()
def delete_address(address_id):
    address = ClientAddress.query.get_or_404(address_id)
    db.session.delete(address)
    db.session.commit()
    return jsonify({"message": f"Address {address_id} deleted"}), 200
