from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.services.weight_pricing import (
    calculate_weight_service_quote,
    load_weight_pricing_config,
)

public_bp = Blueprint("public_bp", __name__, url_prefix="/public")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://",
)


@public_bp.route("/weight-quote", methods=["GET"])
@limiter.limit("100 per minute")
def public_weight_quote():
    weight_lb = request.args.get("weight_lb", type=float)
    has_other_services_raw = request.args.get("has_other_services", default="false", type=str)
    has_other_services_normalized = (has_other_services_raw or "").strip().lower()
    if has_other_services_normalized in ("true", "1", "yes"):
        has_other_services = True
    elif has_other_services_normalized in ("false", "0", "no", ""):
        has_other_services = False
    else:
        has_other_services = None

    if weight_lb is None:
        return jsonify({"error": "weight_lb is required"}), 400
    if weight_lb <= 0:
        return jsonify({"error": "weight_lb must be a positive number"}), 400
    if has_other_services is None:
        return jsonify({"error": "has_other_services must be boolean"}), 400

    try:
        result = calculate_weight_service_quote(
            weight_lb=weight_lb,
            has_other_services=has_other_services,
            pricing_config=load_weight_pricing_config(),
        )
    except (ArithmeticError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result), 200
