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
