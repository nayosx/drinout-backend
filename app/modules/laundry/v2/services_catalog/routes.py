from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.catalog_service import CatalogService
from models.service_category import ServiceCategory
from schemas.catalog_service_schema import CatalogServiceSchema


catalog_service_v2_bp = Blueprint(
    "catalog_service_v2_bp",
    __name__,
    url_prefix="/v2/services",
)

schema = CatalogServiceSchema()
schema_many = CatalogServiceSchema(many=True)


@catalog_service_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    query = CatalogService.query
    category_id = request.args.get("category_id", type=int)
    pricing_mode = request.args.get("pricing_mode")
    is_active = request.args.get("is_active")

    if category_id:
        query = query.filter(CatalogService.category_id == category_id)
    if pricing_mode:
        query = query.filter(CatalogService.pricing_mode == pricing_mode)
    if is_active is not None:
        query = query.filter(CatalogService.is_active == (is_active.lower() == "true"))

    items = query.order_by(CatalogService.sort_order.is_(None), CatalogService.sort_order.asc(), CatalogService.name.asc()).all()
    return jsonify(schema_many.dump(items)), 200


@catalog_service_v2_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = CatalogService.query.get_or_404(item_id)
    return jsonify(schema.dump(item)), 200


@catalog_service_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    category = ServiceCategory.query.get(data["category_id"])
    if not category:
        return jsonify({"error": "Category not found"}), 404

    item = CatalogService(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Service created", "service": schema.dump(item)}), 201


@catalog_service_v2_bp.route("/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update(item_id):
    item = CatalogService.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    if "category_id" in data:
        category = ServiceCategory.query.get(data["category_id"])
        if not category:
            return jsonify({"error": "Category not found"}), 404

    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Service updated", "service": schema.dump(item)}), 200
