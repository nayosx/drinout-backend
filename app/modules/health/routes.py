
from flask import Blueprint, request, jsonify

health_bp = Blueprint("health_bp", __name__, url_prefix="/health")

@health_bp.route("", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200