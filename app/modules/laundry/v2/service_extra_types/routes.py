from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.service_extra_type import ServiceExtraType
from schemas.service_extra_type_schema import ServiceExtraTypeSchema


service_extra_type_bp = Blueprint("service_extra_type_bp", __name__, url_prefix="/v2/service_extra_types")

schema = ServiceExtraTypeSchema()
schema_many = ServiceExtraTypeSchema(many=True)


@service_extra_type_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    items = ServiceExtraType.query.order_by(
        ServiceExtraType.display_order.is_(None),
        ServiceExtraType.display_order.asc(),
        ServiceExtraType.name.asc(),
    ).all()
    return jsonify(schema_many.dump(items)), 200


@service_extra_type_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = ServiceExtraType.query.get_or_404(item_id)
    return jsonify(schema.dump(item)), 200


@service_extra_type_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    item = ServiceExtraType(**data)
    db.session.add(item)
    db.session.commit()

    return jsonify({"message": "Service extra type created", "service_extra_type": schema.dump(item)}), 201


@service_extra_type_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update(item_id):
    item = ServiceExtraType.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    for key, value in data.items():
        setattr(item, key, value)

    db.session.commit()
    return jsonify({"message": "Service extra type updated", "service_extra_type": schema.dump(item)}), 200


@service_extra_type_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = ServiceExtraType.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Service extra type {item_id} deleted"}), 200
