from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.extra import Extra
from models.service_category_legacy import ServiceCategoryLegacy
from models.catalog_service_legacy import CatalogServiceLegacy
from models.service_variant_legacy import ServiceVariantLegacy
from schemas.extra_schema import ExtraSchema
from schemas.service_category_legacy_schema import ServiceCategoryLegacySchema
from schemas.catalog_service_legacy_schema import CatalogServiceLegacySchema
from schemas.service_variant_legacy_schema import ServiceVariantLegacySchema


extras_bp = Blueprint("extras_bp", __name__, url_prefix="/catalog/extras")
service_categories_bp = Blueprint(
    "service_categories_bp",
    __name__,
    url_prefix="/catalog/service-categories",
)
catalog_services_bp = Blueprint(
    "catalog_services_bp",
    __name__,
    url_prefix="/catalog/services",
)
service_variants_bp = Blueprint(
    "service_variants_bp",
    __name__,
    url_prefix="/catalog/service-variants",
)

extra_schema = ExtraSchema()
extras_schema = ExtraSchema(many=True)
service_category_schema = ServiceCategoryLegacySchema()
service_categories_schema = ServiceCategoryLegacySchema(many=True)
catalog_service_schema = CatalogServiceLegacySchema()
catalog_services_schema = CatalogServiceLegacySchema(many=True)
service_variant_schema = ServiceVariantLegacySchema()
service_variants_schema = ServiceVariantLegacySchema(many=True)


def _apply_is_active_filter(query, model):
    is_active = request.args.get("is_active")
    if is_active is None:
        return query
    return query.filter(model.is_active == (is_active.lower() == "true"))


@extras_bp.route("", methods=["GET"])
@jwt_required()
def get_extras():
    query = _apply_is_active_filter(Extra.query, Extra)
    items = query.order_by(Extra.name.asc()).all()
    return jsonify(extras_schema.dump(items)), 200


@extras_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_extra(item_id):
    item = Extra.query.get_or_404(item_id)
    return jsonify(extra_schema.dump(item)), 200


@extras_bp.route("", methods=["POST"])
@jwt_required()
def create_extra():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = extra_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    item = Extra(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Extra created", "extra": extra_schema.dump(item)}), 201


@extras_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_extra(item_id):
    item = Extra.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = extra_schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Extra updated", "extra": extra_schema.dump(item)}), 200


@extras_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_extra(item_id):
    item = Extra.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Extra {item_id} deleted"}), 200


@service_categories_bp.route("", methods=["GET"])
@jwt_required()
def get_service_categories():
    query = _apply_is_active_filter(ServiceCategoryLegacy.query, ServiceCategoryLegacy)
    items = query.order_by(ServiceCategoryLegacy.name.asc()).all()
    return jsonify(service_categories_schema.dump(items)), 200


@service_categories_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_service_category(item_id):
    item = ServiceCategoryLegacy.query.get_or_404(item_id)
    return jsonify(service_category_schema.dump(item)), 200


@service_categories_bp.route("", methods=["POST"])
@jwt_required()
def create_service_category():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = service_category_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    item = ServiceCategoryLegacy(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify(
        {"message": "Service category created", "service_category": service_category_schema.dump(item)}
    ), 201


@service_categories_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_service_category(item_id):
    item = ServiceCategoryLegacy.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = service_category_schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify(
        {"message": "Service category updated", "service_category": service_category_schema.dump(item)}
    ), 200


@service_categories_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_service_category(item_id):
    item = ServiceCategoryLegacy.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Service category {item_id} deleted"}), 200


@catalog_services_bp.route("", methods=["GET"])
@jwt_required()
def get_catalog_services():
    query = _apply_is_active_filter(CatalogServiceLegacy.query, CatalogServiceLegacy)
    category_id = request.args.get("category_id", type=int)
    pricing_mode = request.args.get("pricing_mode")
    if category_id is not None:
        query = query.filter(CatalogServiceLegacy.category_id == category_id)
    if pricing_mode:
        query = query.filter(CatalogServiceLegacy.pricing_mode == pricing_mode.strip().upper())
    items = query.order_by(CatalogServiceLegacy.name.asc()).all()
    return jsonify(catalog_services_schema.dump(items)), 200


@catalog_services_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_catalog_service(item_id):
    item = CatalogServiceLegacy.query.get_or_404(item_id)
    return jsonify(catalog_service_schema.dump(item)), 200


@catalog_services_bp.route("", methods=["POST"])
@jwt_required()
def create_catalog_service():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = catalog_service_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    item = CatalogServiceLegacy(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Catalog service created", "service": catalog_service_schema.dump(item)}), 201


@catalog_services_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_catalog_service(item_id):
    item = CatalogServiceLegacy.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = catalog_service_schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Catalog service updated", "service": catalog_service_schema.dump(item)}), 200


@catalog_services_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_catalog_service(item_id):
    item = CatalogServiceLegacy.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Catalog service {item_id} deleted"}), 200


@service_variants_bp.route("", methods=["GET"])
@jwt_required()
def get_service_variants():
    query = _apply_is_active_filter(ServiceVariantLegacy.query, ServiceVariantLegacy)
    service_id = request.args.get("service_id", type=int)
    if service_id is not None:
        query = query.filter(ServiceVariantLegacy.service_id == service_id)
    items = query.order_by(ServiceVariantLegacy.name.asc()).all()
    return jsonify(service_variants_schema.dump(items)), 200


@service_variants_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_service_variant(item_id):
    item = ServiceVariantLegacy.query.get_or_404(item_id)
    return jsonify(service_variant_schema.dump(item)), 200


@service_variants_bp.route("", methods=["POST"])
@jwt_required()
def create_service_variant():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = service_variant_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    item = ServiceVariantLegacy(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify(
        {"message": "Service variant created", "service_variant": service_variant_schema.dump(item)}
    ), 201


@service_variants_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_service_variant(item_id):
    item = ServiceVariantLegacy.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = service_variant_schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify(
        {"message": "Service variant updated", "service_variant": service_variant_schema.dump(item)}
    ), 200


@service_variants_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_service_variant(item_id):
    item = ServiceVariantLegacy.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Service variant {item_id} deleted"}), 200
