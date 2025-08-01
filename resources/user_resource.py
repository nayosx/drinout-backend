from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from db import db
from models.user import User
from schemas.user_schema import UserSchema
from flask_jwt_extended import jwt_required, get_jwt_identity

user_bp = Blueprint("user_bp", __name__, url_prefix="/users")
user_schema = UserSchema()
user_list_schema = UserSchema(many=True)

@user_bp.route("", methods=["GET"])
@jwt_required()
def get_users():
    role_id = request.args.get("role_id", type=int)
    name = request.args.get("name")
    lite = request.args.get("lite", default="false").lower() == "true"

    query = User.query

    if role_id:
        query = query.filter_by(role_id=role_id)
    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))

    query = query.order_by(User.id)

    if lite:
        users = query.with_entities(User.id, User.name).all()
        result = [{"id": u.id, "name": u.name} for u in users]
        return jsonify(result), 200
    else:
        users = query.all()
        return jsonify(user_list_schema.dump(users)), 200


@user_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user_schema.dump(user)), 200

@user_bp.route("/register", methods=["POST"])
@jwt_required()
def register_user():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = user_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    username = data["username"]
    password = data["password"]
    role_id = data["role_id"]
    phone = data["phone"]
    name = data["name"]
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        password=hashed_password,
        role_id=role_id,
        phone=phone,
        name=name
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        "message": "User registered successfully",
        "user": user_schema.dump(new_user)
    }), 201

@user_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    data = user_schema.load(json_data, partial=True)
    if "username" in data:
        user.username = data["username"]
    if "role_id" in data:
        user.role_id = data["role_id"]
    if "phone" in data:
        user.phone = data["phone"]
    if "name" in data:
        user.name = data["name"]
    db.session.commit()
    return jsonify(user_schema.dump(user)), 200

@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user_id} deleted"}), 200

@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    return jsonify({
        "message": f"Este es el perfil del usuario con ID: {current_user_id}"
    }), 200

@user_bp.route("/<int:user_id>/change-password", methods=["PUT"])
@jwt_required()
def change_password(user_id):
    current_user_id = get_jwt_identity()
    if user_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get_or_404(user_id)
    json_data = request.get_json()

    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    old_password = json_data.get("old_password")
    new_password = json_data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Both old and new passwords are required"}), 400


    if not check_password_hash(user.password, old_password):
        return jsonify({"error": "Incorrect current password"}), 401

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200


@user_bp.route("/<int:user_id>/force-password", methods=["PUT"])
@jwt_required()
def force_change_password(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)

    if current_user.role_id != 1:
        return jsonify({"error": "Only admins can force password changes"}), 403

    user = User.query.get_or_404(user_id)
    json_data = request.get_json()

    if not json_data or "new_password" not in json_data:
        return jsonify({"error": "New password required"}), 400

    user.password = generate_password_hash(json_data["new_password"])
    db.session.commit()

    return jsonify({"message": f"Password updated for user {user.username}"}), 200
