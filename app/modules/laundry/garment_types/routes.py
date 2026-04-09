from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from db import db
from models.garment_type import GarmentType
from schemas.garment_type_schema import GarmentTypeSchema


garment_type_bp = Blueprint("garment_type_bp", __name__, url_prefix="/garment_types")

garment_type_schema = GarmentTypeSchema()
garment_type_list_schema = GarmentTypeSchema(many=True)


@garment_type_bp.route("", methods=["GET"])
@jwt_required()
def get_all_garment_types():
    garment_types = GarmentType.query.order_by(GarmentType.name.asc()).all()
    return jsonify(garment_type_list_schema.dump(garment_types)), 200


@garment_type_bp.route("/<int:garment_type_id>", methods=["GET"])
@jwt_required()
def get_garment_type(garment_type_id):
    garment_type = GarmentType.query.get_or_404(garment_type_id)
    return jsonify(garment_type_schema.dump(garment_type)), 200


@garment_type_bp.route("", methods=["POST"])
@jwt_required()
def create_garment_type():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = garment_type_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    garment_type = GarmentType(name=data["name"], category=data.get("category"))
    db.session.add(garment_type)
    db.session.commit()

    return jsonify({
        "message": "Garment type created",
        "garment_type": garment_type_schema.dump(garment_type),
    }), 201


@garment_type_bp.route("/<int:garment_type_id>", methods=["PUT"])
@jwt_required()
def update_garment_type(garment_type_id):
    garment_type = GarmentType.query.get_or_404(garment_type_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = garment_type_schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if "name" in data:
        garment_type.name = data["name"]
    if "category" in data:
        garment_type.category = data["category"]

    db.session.commit()

    return jsonify({
        "message": "Garment type updated",
        "garment_type": garment_type_schema.dump(garment_type),
    }), 200


@garment_type_bp.route("/<int:garment_type_id>", methods=["DELETE"])
@jwt_required()
def delete_garment_type(garment_type_id):
    garment_type = GarmentType.query.get_or_404(garment_type_id)
    db.session.delete(garment_type)
    db.session.commit()
    return jsonify({"message": f"Garment type {garment_type_id} deleted"}), 200
