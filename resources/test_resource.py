from flask import Blueprint, jsonify

test_bp = Blueprint("test_bp", __name__, url_prefix="/api/v1/test")

@test_bp.route("/", methods=["GET"])
def health_check():
    return jsonify({"message": "API is running"}), 200
