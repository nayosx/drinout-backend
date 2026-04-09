from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.laundry_service_extra import LaundryServiceExtra
from schemas.laundry_service_extra_schema import LaundryServiceExtraSchema


laundry_service_extra_bp = Blueprint(
    "laundry_service_extra_bp",
    __name__,
    url_prefix="/laundry_service_extras",
)

schema = LaundryServiceExtraSchema()
schema_many = LaundryServiceExtraSchema(many=True)


@laundry_service_extra_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    query = LaundryServiceExtra.query
    laundry_service_id = request.args.get("laundry_service_id", type=int)
    extra_id = request.args.get("extra_id", type=int)
    if laundry_service_id is not None:
        query = query.filter(LaundryServiceExtra.laundry_service_id == laundry_service_id)
    if extra_id is not None:
        query = query.filter(LaundryServiceExtra.extra_id == extra_id)
    items = query.order_by(LaundryServiceExtra.id.desc()).all()
    return jsonify(schema_many.dump(items)), 200


@laundry_service_extra_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = LaundryServiceExtra.query.get_or_404(item_id)
    return jsonify(schema.dump(item)), 200


@laundry_service_extra_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    item = LaundryServiceExtra(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Laundry service extra created", "item": schema.dump(item)}), 201


@laundry_service_extra_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update(item_id):
    item = LaundryServiceExtra.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Laundry service extra updated", "item": schema.dump(item)}), 200


@laundry_service_extra_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryServiceExtra.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Laundry service extra {item_id} deleted"}), 200
