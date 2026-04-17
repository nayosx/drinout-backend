from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.client import Client
from models.client_service_type_surcharge_rule import ClientServiceTypeSurchargeRule
from schemas.client_service_type_surcharge_rule_schema import (
    ClientServiceTypeSurchargeRuleSchema,
)


client_service_type_surcharge_rules_bp = Blueprint(
    "client_service_type_surcharge_rules_bp",
    __name__,
    url_prefix="/clients/<int:client_id>/service-type-surcharge-rules",
)

schema = ClientServiceTypeSurchargeRuleSchema()
schema_many = ClientServiceTypeSurchargeRuleSchema(many=True)


def _normalize_service_label(value):
    return str(value or "").strip().upper()


@client_service_type_surcharge_rules_bp.route("", methods=["GET"])
@jwt_required()
def list_client_service_type_surcharge_rules(client_id):
    client = Client.query.get_or_404(client_id)
    if client.is_deleted:
        return jsonify({"error": "Client not found"}), 404

    rules = (
        ClientServiceTypeSurchargeRule.query
        .filter_by(client_id=client_id)
        .order_by(
            ClientServiceTypeSurchargeRule.service_label.asc(),
            ClientServiceTypeSurchargeRule.id.asc(),
        )
        .all()
    )
    return jsonify(schema_many.dump(rules)), 200


@client_service_type_surcharge_rules_bp.route("", methods=["POST"])
@jwt_required()
def create_client_service_type_surcharge_rule(client_id):
    client = Client.query.get_or_404(client_id)
    if client.is_deleted:
        return jsonify({"error": "Client not found"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = schema.load({**json_data, "client_id": client_id})
    service_label = _normalize_service_label(data["service_label"])

    existing_rule = ClientServiceTypeSurchargeRule.query.filter_by(
        client_id=client_id,
        service_label=service_label,
    ).first()
    if existing_rule:
        return jsonify(
            {
                "error": (
                    "A service type surcharge rule already exists for this client and service_label"
                )
            }
        ), 409

    rule = ClientServiceTypeSurchargeRule(
        client_id=client_id,
        service_label=service_label,
        amount=data["amount"],
        is_active=data.get("is_active", True),
        notes=data.get("notes"),
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(schema.dump(rule)), 201


@client_service_type_surcharge_rules_bp.route("/<int:rule_id>", methods=["PUT"])
@jwt_required()
def update_client_service_type_surcharge_rule(client_id, rule_id):
    client = Client.query.get_or_404(client_id)
    if client.is_deleted:
        return jsonify({"error": "Client not found"}), 404

    rule = ClientServiceTypeSurchargeRule.query.filter_by(
        id=rule_id,
        client_id=client_id,
    ).first_or_404()

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    data = schema.load({**json_data, "client_id": client_id}, partial=True)
    if "service_label" in data:
        next_service_label = _normalize_service_label(data["service_label"])
        conflict = (
            ClientServiceTypeSurchargeRule.query
            .filter_by(client_id=client_id, service_label=next_service_label)
            .filter(ClientServiceTypeSurchargeRule.id != rule.id)
            .first()
        )
        if conflict:
            return jsonify(
                {
                    "error": (
                        "A service type surcharge rule already exists for this client and service_label"
                    )
                }
            ), 409
        rule.service_label = next_service_label

    if "amount" in data:
        rule.amount = data["amount"]
    if "is_active" in data:
        rule.is_active = data["is_active"]
    if "notes" in data:
        rule.notes = data["notes"]

    db.session.commit()
    return jsonify(schema.dump(rule)), 200


@client_service_type_surcharge_rules_bp.route("/<int:rule_id>", methods=["DELETE"])
@jwt_required()
def delete_client_service_type_surcharge_rule(client_id, rule_id):
    client = Client.query.get_or_404(client_id)
    if client.is_deleted:
        return jsonify({"error": "Client not found"}), 404

    rule = ClientServiceTypeSurchargeRule.query.filter_by(
        id=rule_id,
        client_id=client_id,
    ).first_or_404()
    db.session.delete(rule)
    db.session.commit()
    return jsonify({"message": f"Client service type surcharge rule {rule_id} deleted"}), 200
