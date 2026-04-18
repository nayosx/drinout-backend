from flask import Blueprint, request, jsonify
import re
import unicodedata
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.menu import Menu
from models.role import Role
from models.user import User
from schemas.menu_schema import MenuSchema
from db import db

menu_bp = Blueprint("menu_bp", __name__, url_prefix="/menus")
menu_schema = MenuSchema(many=True)


def _normalize_menu_key(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return slug or None


def _build_menu_key(payload, menu=None):
    explicit_key = payload.get("key")
    if explicit_key is not None:
        return _normalize_menu_key(explicit_key)

    if menu and menu.key:
        return menu.key

    path_source = payload.get("path")
    if path_source:
        return _normalize_menu_key(str(path_source).strip("/"))

    label_source = payload.get("label")
    if label_source:
        return _normalize_menu_key(label_source)

    if menu and menu.path:
        return _normalize_menu_key(str(menu.path).strip("/"))

    if menu and menu.label:
        return _normalize_menu_key(menu.label)

    return None

def get_current_user_roles():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return []
    return [user.role.id]

def _serialize_menu_node(menu):
    return {
        "id": menu.id,
        "key": menu.key,
        "label": menu.label,
        "path": menu.path,
        "icon": menu.icon,
        "show_in_sidebar": menu.show_in_sidebar,
        "order": menu.order,
        "parent_id": menu.parent_id,
        "created_at": menu.created_at,
        "updated_at": menu.updated_at,
        "children": []
    }

def build_tree(flat_list):
    items = {menu.id: _serialize_menu_node(menu) for menu in flat_list}
    roots = []
    for menu in flat_list:
        current = items[menu.id]
        if menu.parent_id and menu.parent_id in items:
            items[menu.parent_id]["children"].append(current)
        else:
            roots.append(current)
    return roots

@menu_bp.route("", methods=["GET"])
@jwt_required()
def get_menus():
    allowed_roles = get_current_user_roles()
    if not allowed_roles:
        return jsonify([]), 200
    menus_query = (
        Menu.query
        .filter(Menu.show_in_sidebar == True)
        .filter(Menu.roles.any(Role.id.in_(allowed_roles)))
        .order_by(Menu.order)
        .all()
    )
    menu_tree = build_tree(menus_query)
    return jsonify(menu_schema.dump(menu_tree)), 200

@menu_bp.route("/all", methods=["GET"])
@jwt_required()
def get_all_menus():
    menus = Menu.query.order_by(Menu.order).all()
    return jsonify(menu_schema.dump(menus)), 200

@menu_bp.route("", methods=["POST"])
@jwt_required()
def create_menu():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = MenuSchema().load(json_data)
    menu_key = _build_menu_key(data)
    if not menu_key:
        return jsonify({"error": "Menu key could not be generated"}), 400
    if Menu.query.filter_by(key=menu_key).first():
        return jsonify({"error": "Menu key already exists"}), 409
    menu = Menu(
        key=menu_key,
        label=data["label"],
        path=data.get("path"),
        icon=data.get("icon"),
        show_in_sidebar=data.get("show_in_sidebar", True),
        order=data.get("order", 0),
        parent_id=data.get("parent_id")
    )
    db.session.add(menu)
    db.session.commit()
    return jsonify(MenuSchema().dump(menu)), 201

@menu_bp.route("/<int:menu_id>", methods=["PUT"])
@jwt_required()
def update_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    next_key = _build_menu_key(json_data, menu=menu)
    if not next_key:
        return jsonify({"error": "Menu key could not be generated"}), 400
    existing_menu = Menu.query.filter(Menu.key == next_key, Menu.id != menu.id).first()
    if existing_menu:
        return jsonify({"error": "Menu key already exists"}), 409
    menu.key = next_key
    for field in ["label", "path", "icon", "show_in_sidebar", "order", "parent_id"]:
        if field in json_data:
            setattr(menu, field, json_data[field])
    db.session.commit()
    return jsonify(MenuSchema().dump(menu)), 200

@menu_bp.route("/<int:menu_id>", methods=["DELETE"])
@jwt_required()
def delete_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    db.session.delete(menu)
    db.session.commit()
    return jsonify({"message": f"Menu {menu_id} deleted"}), 200

@menu_bp.route("/<int:menu_id>/roles", methods=["POST"])
@jwt_required()
def assign_menu_to_role(menu_id):
    json_data = request.get_json()
    role_id = json_data.get("role_id")
    menu = Menu.query.get_or_404(menu_id)
    role = Role.query.get_or_404(role_id)
    if role not in menu.roles:
        menu.roles.append(role)
        db.session.commit()
    return jsonify({"message": "Role assigned to menu"}), 200

@menu_bp.route("/<int:menu_id>/roles/<int:role_id>", methods=["DELETE"])
@jwt_required()
def remove_menu_from_role(menu_id, role_id):
    menu = Menu.query.get_or_404(menu_id)
    role = Role.query.get_or_404(role_id)
    if role in menu.roles:
        menu.roles.remove(role)
        db.session.commit()
    return jsonify({"message": "Role removed from menu"}), 200


@menu_bp.route("/allwithroles", methods=["GET"])
@jwt_required()
def get_all_menu_roles():
    menus = Menu.query.filter_by(show_in_sidebar=True).order_by(Menu.order).all()

    result = [
        {
            "id": menu.id,
            "key": menu.key,
            "label": menu.label,
            "path": menu.path,
            "icon": menu.icon,
            "show_in_sidebar": menu.show_in_sidebar,
            "order": menu.order,
            "parent_id": menu.parent_id,
            "roles": [role.id for role in menu.roles]
        }
        for menu in menus
    ]

    return jsonify(result), 200
