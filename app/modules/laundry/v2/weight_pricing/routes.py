from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from app.services.weight_pricing import WeightPricingEngine
from models.weight_pricing_profile import WeightPricingProfile
from models.weight_pricing_tier import WeightPricingTier
from schemas.weight_pricing_profile_schema import WeightPricingProfileSchema
from schemas.weight_pricing_tier_schema import WeightPricingTierSchema


weight_pricing_v2_bp = Blueprint(
    "weight_pricing_v2_bp",
    __name__,
    url_prefix="/v2/weight-pricing",
)

profile_schema = WeightPricingProfileSchema()
profile_many = WeightPricingProfileSchema(many=True)
tier_schema = WeightPricingTierSchema()
tier_many = WeightPricingTierSchema(many=True)


@weight_pricing_v2_bp.route("/profiles", methods=["GET"])
@jwt_required()
def get_profiles():
    query = WeightPricingProfile.query
    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(WeightPricingProfile.is_active == (is_active.lower() == "true"))
    items = query.order_by(WeightPricingProfile.id.asc()).all()
    return jsonify(profile_many.dump(items)), 200


@weight_pricing_v2_bp.route("/profiles/<int:item_id>", methods=["GET"])
@jwt_required()
def get_profile(item_id):
    item = WeightPricingProfile.query.get_or_404(item_id)
    return jsonify(profile_schema.dump(item)), 200


@weight_pricing_v2_bp.route("/profiles", methods=["POST"])
@jwt_required()
def create_profile():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = profile_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    item = WeightPricingProfile(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Weight pricing profile created", "weight_pricing_profile": profile_schema.dump(item)}), 201


@weight_pricing_v2_bp.route("/profiles/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update_profile(item_id):
    item = WeightPricingProfile.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = profile_schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Weight pricing profile updated", "weight_pricing_profile": profile_schema.dump(item)}), 200


@weight_pricing_v2_bp.route("/tiers", methods=["GET"])
@jwt_required()
def get_tiers():
    query = WeightPricingTier.query
    profile_id = request.args.get("profile_id", type=int)
    is_active = request.args.get("is_active")
    if profile_id:
        query = query.filter(WeightPricingTier.profile_id == profile_id)
    if is_active is not None:
        query = query.filter(WeightPricingTier.is_active == (is_active.lower() == "true"))
    items = query.order_by(WeightPricingTier.profile_id.asc(), WeightPricingTier.sort_order.asc()).all()
    return jsonify(tier_many.dump(items)), 200


@weight_pricing_v2_bp.route("/tiers/<int:item_id>", methods=["GET"])
@jwt_required()
def get_tier(item_id):
    item = WeightPricingTier.query.get_or_404(item_id)
    return jsonify(tier_schema.dump(item)), 200


@weight_pricing_v2_bp.route("/tiers", methods=["POST"])
@jwt_required()
def create_tier():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = tier_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    profile = WeightPricingProfile.query.get(data["profile_id"])
    if not profile:
        return jsonify({"error": "Weight pricing profile not found"}), 404

    item = WeightPricingTier(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Weight pricing tier created", "weight_pricing_tier": tier_schema.dump(item)}), 201


@weight_pricing_v2_bp.route("/tiers/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update_tier(item_id):
    item = WeightPricingTier.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = tier_schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    if "profile_id" in data:
        profile = WeightPricingProfile.query.get(data["profile_id"])
        if not profile:
            return jsonify({"error": "Weight pricing profile not found"}), 404

    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Weight pricing tier updated", "weight_pricing_tier": tier_schema.dump(item)}), 200


@weight_pricing_v2_bp.route("/quote", methods=["POST"])
@jwt_required()
def quote():
    json_data = request.get_json() or {}
    weight_lb = json_data.get("weight_lb")
    profile_id = json_data.get("profile_id")
    if weight_lb is None:
        return jsonify({"error": "weight_lb is required"}), 400

    try:
        engine = WeightPricingEngine.from_profile_id(profile_id)
        result = engine.quote(weight_lb)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result), 200
