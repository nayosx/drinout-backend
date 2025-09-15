from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, func
import re
from db import db
from models.client import Client, ClientPhone
from schemas.client_schema import (
    ClientSchema,
    ClientShortSchema,
    ClientDetailSchema
)

clients_bp = Blueprint("clients_bp", __name__, url_prefix="/clients")

client_schema = ClientSchema()
client_short_list_schema = ClientShortSchema(many=True)
client_detail_schema = ClientDetailSchema()
client_detail_list_schema = ClientDetailSchema(many=True)

def apply_common_filters(query, q):
    if q:
        digits = re.sub(r"\D+", "", q)
        name_cond = Client.name.ilike(f"%{q}%")
        if digits:
            norm = func.replace(ClientPhone.phone_number, "-", "")
            norm = func.replace(norm, " ", "")
            norm = func.replace(norm, "(", "")
            norm = func.replace(norm, ")", "")
            norm = func.replace(norm, "+", "")
            query = query.join(ClientPhone, ClientPhone.client_id == Client.id, isouter=True).filter(
                or_(name_cond, norm.like(f"%{digits}%"), ClientPhone.phone_number.ilike(f"%{q}%"))
            ).distinct()
        else:
            query = query.filter(name_cond)
    return query

@clients_bp.route("", methods=["GET"])
@jwt_required()
def get_clients():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    q = request.args.get("q", None, type=str)
    detail = request.args.get("detail", "false").lower() in ("1", "true", "yes")

    query = Client.query.filter_by(is_deleted=False)
    query = apply_common_filters(query, q)

    if detail:
        query = query.options(selectinload(Client.addresses), selectinload(Client.phones))

    query = query.order_by(Client.id)

    if per_page == 0:
        clients = query.all()
        items = client_detail_list_schema.dump(clients) if detail else client_short_list_schema.dump(clients)
        return jsonify({
            "total": len(items),
            "pages": 1,
            "current_page": 1,
            "per_page": 0,
            "items": items
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    clients = pagination.items
    items = client_detail_list_schema.dump(clients) if detail else client_short_list_schema.dump(clients)
    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page,
        "items": items
    }), 200

@clients_bp.route("/lite", methods=["GET"])
@jwt_required()
def get_clients_lite():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    q = request.args.get("q", None, type=str)

    query = Client.query.filter_by(is_deleted=False)
    query = apply_common_filters(query, q)
    query = query.order_by(Client.id)

    if per_page == 0:
        clients = query.all()
        items = client_short_list_schema.dump(clients)
        return jsonify({
            "total": len(items),
            "pages": 1,
            "current_page": 1,
            "per_page": 0,
            "items": items
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    clients = pagination.items
    items = client_short_list_schema.dump(clients)
    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page,
        "items": items
    }), 200

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
