from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.role import Role
from models.user import User
from schemas.role_schema import RoleSchema
from schemas.user_schema import UserSchema

role_bp = Blueprint("role_bp", __name__, url_prefix="/roles")
role_schema = RoleSchema()
role_list_schema = RoleSchema(many=True)
user_list_schema = UserSchema(many=True)

@role_bp.route("", methods=["GET"])
@jwt_required()
def get_roles():
    roles = Role.query.order_by(Role.id).all()
    return jsonify(role_list_schema.dump(roles)), 200

@role_bp.route("/<int:role_id>", methods=["GET"])
@jwt_required()
def get_role(role_id):
    role = Role.query.get_or_404(role_id)
    return jsonify(role_schema.dump(role)), 200

@role_bp.route("", methods=["POST"])
@jwt_required()
def create_role():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = role_schema.load(json_data)
    role = Role(name=data["name"], description=data["description"])
    db.session.add(role)
    db.session.commit()
    return jsonify(role_schema.dump(role)), 201

@role_bp.route("/<int:role_id>", methods=["PUT"])
@jwt_required()
def update_role(role_id):
    role = Role.query.get_or_404(role_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = role_schema.load(json_data, partial=True)
    if "name" in data:
        role.name = data["name"]
    if "description" in data:
        role.description = data["description"]
    db.session.commit()
    return jsonify(role_schema.dump(role)), 200

@role_bp.route("/<int:role_id>", methods=["DELETE"])
@jwt_required()
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    return jsonify({"message": f"Role {role_id} deleted"}), 200

@role_bp.route("/<int:role_id>/users", methods=["GET"])
@jwt_required()
def get_role_users(role_id):
    role = Role.query.get_or_404(role_id)
    users = User.query.filter_by(role_id=role.id).all()
    return jsonify(user_list_schema.dump(users)), 200
