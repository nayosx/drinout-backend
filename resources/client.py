from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.client import Client
from schemas.client import (
    ClientSchema,
    ClientShortSchema,
    ClientDetailSchema
)

clients_bp = Blueprint("clients_bp", __name__, url_prefix="/clients")

client_schema = ClientSchema()
client_short_schema = ClientShortSchema(many=True)
client_detail_schema = ClientDetailSchema()

@clients_bp.route("", methods=["GET"])
@jwt_required()
def get_clients():
    # Parámetros
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    q = request.args.get("q", None, type=str)

    # Base query
    query = Client.query.filter_by(is_deleted=False)

    # Filtro por nombre
    if q:
        query = query.filter(Client.name.ilike(f"%{q}%"))

    query = query.order_by(Client.id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    clients = pagination.items
    response = {
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page,
        "items": client_short_schema.dump(clients)
    }
    return jsonify(response), 200

@clients_bp.route("/<int:client_id>", methods=["GET"])
@jwt_required()
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.is_deleted:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(client_detail_schema.dump(client)), 200

@clients_bp.route("", methods=["POST"])
@jwt_required()
def create_client():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = client_schema.load(json_data)
    client = Client(
        name=data["name"],
        email=data.get("email"),
        document_id=data.get("document_id")
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(client_schema.dump(client)), 201

@clients_bp.route("/<int:client_id>", methods=["PUT"])
@jwt_required()
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.is_deleted:
        return jsonify({"error": "Client not found"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = client_schema.load(json_data, partial=True)
    if "name" in data:
        client.name = data["name"]
    if "email" in data:
        client.email = data["email"]
    if "document_id" in data:
        client.document_id = data["document_id"]
    db.session.commit()
    return jsonify(client_schema.dump(client)), 200

@clients_bp.route("/<int:client_id>", methods=["DELETE"])
@jwt_required()
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.is_deleted:
        return jsonify({"error": "Client already deleted"}), 400
    client.is_deleted = True
    db.session.commit()
    return jsonify({"message": f"Client {client_id} logically deleted"}), 200
