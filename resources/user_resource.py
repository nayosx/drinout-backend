from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from db import db
from models.user import User
from schemas.user_schema import UserSchema
from flask_jwt_extended import jwt_required, get_jwt_identity

user_bp = Blueprint("user_bp", __name__, url_prefix="/users")

@user_bp.route("", methods=["GET"])
@jwt_required()
def get_users():
    users = User.query.all()
    user_schema = UserSchema(many=True)
    return jsonify(user_schema.dump(users)), 200

@user_bp.route("/register", methods=["POST"])
@jwt_required()
def register_user():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    user_schema = UserSchema()
    try:
        data = user_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    username = data["username"]
    password = data["password"]
    role_id = data["role_id"]

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    hashed_password = generate_password_hash(password)

    new_user = User(
        username=username,
        password=hashed_password,
        role_id=role_id
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user": user_schema.dump(new_user)
    }), 201

@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    return jsonify({
        "message": f"Este es el perfil del usuario con ID: {current_user_id}"
    }), 200
