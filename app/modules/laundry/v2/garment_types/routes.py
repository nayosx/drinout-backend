from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.garment_type import GarmentType
from schemas.garment_type_v2_schema import GarmentTypeV2Schema


garment_type_v2_bp = Blueprint("garment_type_v2_bp", __name__, url_prefix="/v2/garment_types")

schema = GarmentTypeV2Schema()
schema_many = GarmentTypeV2Schema(many=True)


@garment_type_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    garment_types = GarmentType.query.order_by(
        GarmentType.display_order.is_(None),
        GarmentType.display_order.asc(),
        GarmentType.name.asc(),
    ).all()
    return jsonify(schema_many.dump(garment_types)), 200


@garment_type_v2_bp.route("/<int:garment_type_id>", methods=["GET"])
@jwt_required()
def get_one(garment_type_id):
    garment_type = GarmentType.query.get_or_404(garment_type_id)
    return jsonify(schema.dump(garment_type)), 200


@garment_type_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    garment_type = GarmentType(**data)
    db.session.add(garment_type)
    db.session.commit()

    return jsonify({"message": "Garment type created", "garment_type": schema.dump(garment_type)}), 201


@garment_type_v2_bp.route("/<int:garment_type_id>", methods=["PUT"])
@jwt_required()
def update(garment_type_id):
    garment_type = GarmentType.query.get_or_404(garment_type_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    for key, value in data.items():
        setattr(garment_type, key, value)

    db.session.commit()
    return jsonify({"message": "Garment type updated", "garment_type": schema.dump(garment_type)}), 200


@garment_type_v2_bp.route("/<int:garment_type_id>", methods=["DELETE"])
@jwt_required()
def delete(garment_type_id):
    garment_type = GarmentType.query.get_or_404(garment_type_id)
    db.session.delete(garment_type)
    db.session.commit()
    return jsonify({"message": f"Garment type {garment_type_id} deleted"}), 200
