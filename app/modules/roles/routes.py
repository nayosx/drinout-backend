from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.menu import Menu
from models.role import Role
from models.user import User
from schemas.role_schema import RoleSchema
from schemas.user_schema import UserSchema

role_bp = Blueprint("role_bp", __name__, url_prefix="/roles")
role_schema = RoleSchema()
role_list_schema = RoleSchema(many=True)
user_list_schema = UserSchema(many=True)


def _serialize_role_brief(role):
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
    }


def _serialize_menu_catalog_item(menu):
    return {
        "id": menu.id,
        "key": menu.key,
        "label": menu.label,
        "path": menu.path,
        "icon": menu.icon,
        "show_in_sidebar": menu.show_in_sidebar,
        "order": menu.order,
        "parent_id": menu.parent_id,
    }

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


@role_bp.route("/<int:role_id>/menus", methods=["GET"])
@jwt_required()
def get_role_menus(role_id):
    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return jsonify({"error": "Role not found"}), 404

    catalog = Menu.query.filter_by(show_in_sidebar=True).order_by(Menu.order, Menu.id).all()
    assigned_menu_keys = [menu.key for menu in role.menus if menu.show_in_sidebar]

    return jsonify({
        "role": _serialize_role_brief(role),
        "catalog": [_serialize_menu_catalog_item(menu) for menu in catalog],
        "assigned_menu_keys": assigned_menu_keys,
    }), 200


@role_bp.route("/<int:role_id>/menus", methods=["PUT"])
@jwt_required()
def update_role_menus(role_id):
    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return jsonify({"error": "Role not found"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    menu_keys = json_data.get("menu_keys")
    if not isinstance(menu_keys, list):
        return jsonify({"error": "menu_keys is required"}), 400

    normalized_menu_keys = []
    for value in menu_keys:
        if not isinstance(value, str):
            return jsonify({"error": "menu_keys must be a list of strings"}), 400
        key = value.strip()
        if not key:
            return jsonify({"error": "menu_keys must not contain empty values"}), 400
        if key not in normalized_menu_keys:
            normalized_menu_keys.append(key)

    catalog = Menu.query.filter_by(show_in_sidebar=True).order_by(Menu.order, Menu.id).all()
    catalog_by_key = {menu.key: menu for menu in catalog}

    invalid_menu_keys = [key for key in normalized_menu_keys if key not in catalog_by_key]
    if invalid_menu_keys:
        return jsonify({
            "error": "Unknown menu keys",
            "invalid_menu_keys": invalid_menu_keys,
        }), 400

    selected_keys = set(normalized_menu_keys)
    for key in normalized_menu_keys:
        menu = catalog_by_key[key]
        if menu.parent_id:
            parent_menu = next((item for item in catalog if item.id == menu.parent_id), None)
            if parent_menu and parent_menu.key not in selected_keys:
                return jsonify({
                    "error": "Child menu requires parent menu",
                    "menu_key": menu.key,
                    "required_parent_key": parent_menu.key,
                }), 409

    role.menus = [catalog_by_key[key] for key in normalized_menu_keys]
    db.session.commit()

    return jsonify({
        "message": "Role menus updated successfully",
        "role_id": role.id,
        "assigned_menu_keys": normalized_menu_keys,
    }), 200
