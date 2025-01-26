# resources/auth_resource.py
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)

from db import db
from models.user import User
from schemas.user_schema import UserSchema

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    if not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user_data
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()  
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        "message": "Token refreshed",
        "access_token": new_access_token
    }), 200
