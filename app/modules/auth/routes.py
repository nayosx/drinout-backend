from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    decode_token
)
from datetime import datetime
from db import db
from models.user import User
from models.refresh_token import RefreshToken
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

    # Decodificar el refresh token para obtener jti y exp
    decoded_refresh = decode_token(refresh_token)
    refresh_jti = decoded_refresh["jti"]
    expires = decoded_refresh["exp"]

    # Guardar el refresh token en DB
    db.session.add(RefreshToken(
        jti=refresh_jti,
        user_id=user.id,
        expires_at=datetime.utcfromtimestamp(expires)
    ))
    db.session.commit()

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
    jti = get_jwt()["jti"]

    # Validar que el token no esté revocado
    stored_token = RefreshToken.query.filter_by(jti=jti, revoked=False).first()
    if not stored_token:
        return jsonify({"error": "Refresh token is revoked or invalid"}), 401

    new_access_token = create_access_token(identity=current_user_id)

    return jsonify({
        "message": "Token refreshed",
        "access_token": new_access_token
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    jti = get_jwt()["jti"]
    stored_token = RefreshToken.query.filter_by(jti=jti, revoked=False).first()

    if stored_token:
        stored_token.revoked = True
        db.session.commit()

    return jsonify({"message": "Logout successful"}), 200
