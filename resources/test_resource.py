from flask import Blueprint, jsonify

test_bp = Blueprint("test_bp", __name__, url_prefix="/s")

@test_bp.route("/", methods=["GET"])
def health_check():
    return jsonify({"message": "API is running"}), 200
