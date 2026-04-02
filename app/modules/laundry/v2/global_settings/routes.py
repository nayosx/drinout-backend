from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.global_setting import GlobalSetting
from schemas.global_setting_schema import GlobalSettingSchema


global_setting_v2_bp = Blueprint(
    "global_setting_v2_bp",
    __name__,
    url_prefix="/v2/global-settings",
)

schema = GlobalSettingSchema()
schema_many = GlobalSettingSchema(many=True)


@global_setting_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    query = GlobalSetting.query
    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(GlobalSetting.is_active == (is_active.lower() == "true"))
    items = query.order_by(GlobalSetting.key.asc()).all()
    return jsonify(schema_many.dump(items)), 200


@global_setting_v2_bp.route("/<string:item_key>", methods=["GET"])
@jwt_required()
def get_one(item_key):
    item = GlobalSetting.query.filter_by(key=item_key).first_or_404()
    return jsonify(schema.dump(item)), 200


@global_setting_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    item = GlobalSetting(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Global setting created", "global_setting": schema.dump(item)}), 201


@global_setting_v2_bp.route("/<string:item_key>", methods=["PATCH"])
@jwt_required()
def update(item_key):
    item = GlobalSetting.query.filter_by(key=item_key).first_or_404()
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
    return jsonify({"message": "Global setting updated", "global_setting": schema.dump(item)}), 200
