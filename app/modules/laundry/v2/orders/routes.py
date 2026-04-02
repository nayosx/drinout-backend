import json
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.orm import selectinload

from db import db
from app.services.weight_pricing import WeightPricingEngine
from models.catalog_service import CatalogService
from models.client import Client, ClientAddress
from models.delivery_zone import DeliveryZone, DeliveryZonePrice
from models.extra_catalog import ExtraCatalog
from models.order import Order
from models.order_extra_item import OrderExtraItem
from models.order_item import OrderItem
from models.order_status_history import OrderStatusHistory
from models.order_weight_pricing_snapshot import OrderWeightPricingSnapshot
from models.payment_type import PaymentType
from models.service_price_option import ServicePriceOption
from models.user import User
from models.weight_pricing_profile import WeightPricingProfile
from schemas.order_schema import OrderCreateSchema, OrderPatchSchema, OrderSchema


order_v2_bp = Blueprint(
    "order_v2_bp",
    __name__,
    url_prefix="/v2/orders",
)

schema = OrderSchema()
schema_many = OrderSchema(many=True)
create_schema = OrderCreateSchema()
patch_schema = OrderPatchSchema()


def money(value):
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        amount = value
    else:
        amount = Decimal(str(value))
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _order_query():
    return Order.query.options(
        selectinload(Order.items).selectinload(OrderItem.weight_pricing_snapshot),
        selectinload(Order.extra_items),
        selectinload(Order.status_history),
        selectinload(Order.pricing_profile),
        selectinload(Order.payment_type),
        selectinload(Order.delivery_zone),
        selectinload(Order.delivery_zone_price),
        selectinload(Order.client),
        selectinload(Order.client_address),
    )


def _active_zone_price(zone_id):
    return (
        DeliveryZonePrice.query.filter(
            DeliveryZonePrice.delivery_zone_id == zone_id,
            DeliveryZonePrice.is_active.is_(True),
            DeliveryZonePrice.effective_to.is_(None),
        )
        .order_by(DeliveryZonePrice.effective_from.desc(), DeliveryZonePrice.id.desc())
        .first()
    )


def _latest_delivery_order(client_id, client_address_id=None):
    query = Order.query.filter(Order.client_id == client_id)
    if client_address_id is not None:
        query = query.filter(Order.client_address_id == client_address_id)

    query = query.filter(
        (Order.delivery_zone_id.isnot(None))
        | (Order.delivery_fee_suggested > Decimal("0.00"))
        | (Order.delivery_fee_final > Decimal("0.00"))
    )

    return query.order_by(Order.created_at.desc(), Order.id.desc()).first()


def _validate_client(client_id, client_address_id):
    client = Client.query.get(client_id)
    if not client:
        return None, None, ({"error": "Client not found"}, 404)

    address = None
    if client_address_id is not None:
        address = ClientAddress.query.get(client_address_id)
        if not address or address.client_id != client_id:
            return None, None, ({"error": "Address does not belong to client"}, 400)
    return client, address, None


def _validate_user(user_id, field_name):
    if user_id is None:
        return None
    user = User.query.get(user_id)
    if not user:
        return {"error": f"{field_name} user not found"}, 404
    return None


def _validate_payment_type(payment_type_id):
    payment_type = PaymentType.query.get(payment_type_id)
    if not payment_type:
        return None, ({"error": "Payment type not found"}, 404)
    if not payment_type.is_active:
        return None, ({"error": "Payment type is inactive"}, 400)
    return payment_type, None


def _resolve_profile(profile_id):
    if profile_id:
        profile = WeightPricingProfile.query.get(profile_id)
        if not profile:
            return None, ({"error": "Weight pricing profile not found"}, 404)
        return profile, None
    profile = (
        WeightPricingProfile.query.filter_by(is_active=True)
        .order_by(WeightPricingProfile.id.asc())
        .first()
    )
    return profile, None


def _calculate_payment_surcharge(base_total, payment_type):
    surcharge_value = money(payment_type.surcharge_value)
    if payment_type.surcharge_type == "FIXED":
        surcharge_amount = money(surcharge_value)
    else:
        surcharge_amount = money(base_total * (Decimal(str(payment_type.surcharge_value)) / Decimal("100")))
    return surcharge_amount


def _calculate_line_subtotal(quantity, unit_price, discount_amount):
    subtotal_before_discount = money(quantity * unit_price)
    subtotal_after_discount = money(subtotal_before_discount - discount_amount)
    if subtotal_after_discount < 0:
        raise ValueError("Discount amount cannot exceed line subtotal")
    return subtotal_before_discount, subtotal_after_discount


def _build_order_items(order, items_data, pricing_profile, current_user_id):
    service_subtotal = Decimal("0.00")
    item_models = []
    snapshot_models = []

    for row in items_data:
        service = CatalogService.query.get(row["service_id"])
        if not service:
            return None, None, ({"error": f"Service {row['service_id']} not found"}, 404)

        quantity = money(row.get("quantity", 1))
        discount_amount = money(row.get("discount_amount", 0))
        suggested_option = None
        suggested_unit_price = None
        suggested_price_label = None
        recommended_unit_price = None
        final_unit_price = row.get("final_unit_price")
        manual_override_reason = row.get("manual_price_override_reason")

        if row.get("suggested_price_option_id") is not None:
            suggested_option = ServicePriceOption.query.get(row["suggested_price_option_id"])
            if not suggested_option or suggested_option.service_id != service.id:
                return None, None, ({"error": "Suggested price option does not belong to the service"}, 400)
            suggested_unit_price = money(suggested_option.suggested_price)
            suggested_price_label = suggested_option.label

        snapshot_model = None

        if service.pricing_mode == "WEIGHT":
            weight_lb = row.get("weight_lb")
            if weight_lb is None:
                return None, None, ({"error": f"weight_lb is required for service {service.id}"}, 400)
            if not pricing_profile:
                return None, None, ({"error": "No weight pricing profile available"}, 400)

            quote = WeightPricingEngine(pricing_profile).quote(weight_lb)
            recommended_unit_price = money(quote["recommended_price"])
            if final_unit_price is None:
                final_unit_price = recommended_unit_price
            else:
                final_unit_price = money(final_unit_price)
                if final_unit_price != recommended_unit_price and not pricing_profile.allow_manual_override:
                    return None, None, ({"error": "Manual override is not allowed for the selected weight pricing profile"}, 400)
                if final_unit_price != recommended_unit_price and not manual_override_reason:
                    return None, None, ({"error": "manual_price_override_reason is required when overriding weight pricing"}, 400)

            quantity = Decimal("1.00")
            subtotal_before_discount, subtotal_after_discount = _calculate_line_subtotal(
                quantity,
                final_unit_price,
                discount_amount,
            )
            item = OrderItem(
                service_id=service.id,
                suggested_price_option_id=suggested_option.id if suggested_option else None,
                service_name_snapshot=service.name,
                category_name_snapshot=service.category.name if service.category else "",
                pricing_mode=service.pricing_mode,
                quantity=quantity,
                weight_lb=money(weight_lb),
                unit_label_snapshot="servicio",
                suggested_price_label_snapshot=suggested_price_label,
                suggested_unit_price=suggested_unit_price,
                recommended_unit_price=recommended_unit_price,
                final_unit_price=final_unit_price,
                manual_price_override_by_user_id=current_user_id if final_unit_price != recommended_unit_price else None,
                manual_price_override_reason=manual_override_reason if final_unit_price != recommended_unit_price else None,
                discount_amount=discount_amount,
                subtotal_before_discount=subtotal_before_discount,
                subtotal_after_discount=subtotal_after_discount,
                notes=row.get("notes"),
            )
            snapshot_model = OrderWeightPricingSnapshot(
                order=order,
                pricing_profile_id=quote["profile_id"],
                pricing_profile_name_snapshot=quote["profile_name"],
                strategy_applied=quote["strategy_selected"],
                weight_lb=money(weight_lb),
                selected_tier_id=quote["selected_tier_id"],
                selected_tier_max_weight_lb=money(quote["selected_tier_max_weight_lb"]) if quote["selected_tier_max_weight_lb"] is not None else None,
                selected_base_price=money(quote["selected_base_price"]) if quote["selected_base_price"] is not None else None,
                recommended_price=recommended_unit_price,
                final_price=final_unit_price,
                override_applied=final_unit_price != recommended_unit_price,
                override_by_user_id=current_user_id if final_unit_price != recommended_unit_price else None,
                override_reason=manual_override_reason if final_unit_price != recommended_unit_price else None,
                allow_manual_override=quote["allow_manual_override"],
                decision_reason=quote["decision_reason"],
                options_evaluated_json=json.dumps(quote["options_evaluated"], ensure_ascii=True),
                lowest_valid_price=money(quote["lowest_valid_price"]),
                highest_valid_price=money(quote["highest_valid_price"]),
                difference_selected_vs_lowest=money(quote["difference_selected_vs_lowest"]),
                difference_selected_vs_highest=money(quote["difference_selected_vs_highest"]),
            )
        else:
            recommended_unit_price = suggested_unit_price
            if final_unit_price is None:
                if suggested_unit_price is None:
                    return None, None, ({"error": f"final_unit_price or suggested_price_option_id is required for service {service.id}"}, 400)
                final_unit_price = suggested_unit_price
            else:
                final_unit_price = money(final_unit_price)

            if final_unit_price != (recommended_unit_price if recommended_unit_price is not None else final_unit_price):
                if not service.allow_manual_price_override:
                    return None, None, ({"error": f"Manual override is not allowed for service {service.id}"}, 400)
                if not manual_override_reason:
                    return None, None, ({"error": "manual_price_override_reason is required when overriding service price"}, 400)

            subtotal_before_discount, subtotal_after_discount = _calculate_line_subtotal(
                quantity,
                final_unit_price,
                discount_amount,
            )
            item = OrderItem(
                service_id=service.id,
                suggested_price_option_id=suggested_option.id if suggested_option else None,
                service_name_snapshot=service.name,
                category_name_snapshot=service.category.name if service.category else "",
                pricing_mode=service.pricing_mode,
                quantity=quantity,
                weight_lb=None,
                unit_label_snapshot=service.unit_label,
                suggested_price_label_snapshot=suggested_price_label,
                suggested_unit_price=suggested_unit_price,
                recommended_unit_price=recommended_unit_price,
                final_unit_price=final_unit_price,
                manual_price_override_by_user_id=(
                    current_user_id if recommended_unit_price is not None and final_unit_price != recommended_unit_price else None
                ),
                manual_price_override_reason=(
                    manual_override_reason if recommended_unit_price is not None and final_unit_price != recommended_unit_price else None
                ),
                discount_amount=discount_amount,
                subtotal_before_discount=subtotal_before_discount,
                subtotal_after_discount=subtotal_after_discount,
                notes=row.get("notes"),
            )

        service_subtotal += item.subtotal_after_discount
        item_models.append(item)
        if snapshot_model:
            snapshot_models.append((item, snapshot_model))

    return item_models, snapshot_models, service_subtotal


def _build_extra_items(extras_data):
    extras_subtotal = Decimal("0.00")
    extra_models = []

    for row in extras_data:
        extra = ExtraCatalog.query.get(row["extra_id"])
        if not extra:
            return None, None, ({"error": f"Extra {row['extra_id']} not found"}, 404)

        quantity = money(row.get("quantity", 1))
        discount_amount = money(row.get("discount_amount", 0))
        suggested_unit_price = money(extra.suggested_unit_price)
        final_unit_price = money(row.get("final_unit_price", suggested_unit_price))
        subtotal_before_discount, subtotal_after_discount = _calculate_line_subtotal(
            quantity,
            final_unit_price,
            discount_amount,
        )
        item = OrderExtraItem(
            extra_id=extra.id,
            extra_name_snapshot=extra.name,
            unit_label_snapshot=extra.unit_label,
            quantity=quantity,
            suggested_unit_price=suggested_unit_price,
            final_unit_price=final_unit_price,
            discount_amount=discount_amount,
            subtotal_before_discount=subtotal_before_discount,
            subtotal_after_discount=subtotal_after_discount,
            notes=row.get("notes"),
        )
        extras_subtotal += item.subtotal_after_discount
        extra_models.append(item)

    return extra_models, extras_subtotal, None


def _create_status_history(order, previous_status, new_status, user_id, reason=None):
    history = OrderStatusHistory(
        order=order,
        previous_status=previous_status,
        new_status=new_status,
        changed_by_user_id=user_id,
        reason=reason,
    )
    db.session.add(history)


@order_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    client_id = request.args.get("client_id", type=int)
    status = request.args.get("status")
    charged_by_user_id = request.args.get("charged_by_user_id", type=int)

    query = _order_query()
    if client_id:
        query = query.filter(Order.client_id == client_id)
    if status:
        query = query.filter(Order.status == status)
    if charged_by_user_id:
        query = query.filter(Order.charged_by_user_id == charged_by_user_id)

    pagination = query.order_by(Order.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": schema_many.dump(pagination.items),
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }
    ), 200


@order_v2_bp.route("/delivery-fee-suggestion", methods=["GET"])
@jwt_required()
def get_delivery_fee_suggestion():
    client_id = request.args.get("client_id", type=int)
    client_address_id = request.args.get("client_address_id", type=int)
    delivery_zone_id = request.args.get("delivery_zone_id", type=int)

    if client_id is None:
        return jsonify({"error": "client_id is required"}), 400

    _, _, validation_error = _validate_client(client_id, client_address_id)
    if validation_error:
        payload, status_code = validation_error
        return jsonify(payload), status_code

    delivery_zone = None
    delivery_zone_price = None
    delivery_fee_suggested_by_zone = Decimal("0.00")
    if delivery_zone_id is not None:
        delivery_zone = DeliveryZone.query.get(delivery_zone_id)
        if not delivery_zone:
            return jsonify({"error": "Delivery zone not found"}), 404
        delivery_zone_price = _active_zone_price(delivery_zone_id)
        if delivery_zone_price:
            delivery_fee_suggested_by_zone = money(delivery_zone_price.fee_amount)

    last_order_for_address = None
    if client_address_id is not None:
        last_order_for_address = _latest_delivery_order(client_id, client_address_id)
    last_order_for_client = _latest_delivery_order(client_id)

    last_delivery_fee_for_address = money(last_order_for_address.delivery_fee_final) if last_order_for_address else Decimal("0.00")
    last_delivery_fee_for_client = money(last_order_for_client.delivery_fee_final) if last_order_for_client else Decimal("0.00")
    initial_delivery_fee_final = (
        last_delivery_fee_for_address
        if last_order_for_address
        else last_delivery_fee_for_client
    )

    return jsonify(
        {
            "client_id": client_id,
            "client_address_id": client_address_id,
            "delivery_zone_id": delivery_zone_id,
            "delivery_zone_name": delivery_zone.name if delivery_zone else None,
            "delivery_zone_price_id": delivery_zone_price.id if delivery_zone_price else None,
            "delivery_fee_suggested_by_zone": str(delivery_fee_suggested_by_zone),
            "last_delivery_fee_final_for_client_address": str(last_delivery_fee_for_address),
            "last_delivery_fee_final_for_client": str(last_delivery_fee_for_client),
            "last_delivery_order_id_for_client_address": last_order_for_address.id if last_order_for_address else None,
            "last_delivery_order_id_for_client": last_order_for_client.id if last_order_for_client else None,
            "has_previous_delivery_for_client_address": last_order_for_address is not None,
            "has_previous_delivery_for_client": last_order_for_client is not None,
            "initial_delivery_fee_final": str(initial_delivery_fee_final),
        }
    ), 200


@order_v2_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = _order_query().filter(Order.id == item_id).first_or_404()
    return jsonify(schema.dump(item)), 200


@order_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = create_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    current_user_id = get_jwt_identity()

    _, _, validation_error = _validate_client(data["client_id"], data.get("client_address_id"))
    if validation_error:
        payload, status_code = validation_error
        return jsonify(payload), status_code

    charged_by_user_id = data.get("charged_by_user_id") or current_user_id
    user_error = _validate_user(charged_by_user_id, "charged_by")
    if user_error:
        payload, status_code = user_error
        return jsonify(payload), status_code

    pricing_profile, profile_error = _resolve_profile(data.get("pricing_profile_id"))
    if profile_error:
        payload, status_code = profile_error
        return jsonify(payload), status_code

    payment_type, payment_type_error = _validate_payment_type(data["payment_type_id"])
    if payment_type_error:
        payload, status_code = payment_type_error
        return jsonify(payload), status_code

    delivery_zone = None
    delivery_zone_price = None
    delivery_fee_suggested = Decimal("0.00")
    delivery_fee_final = Decimal("0.00")
    if data.get("delivery_zone_id") is not None:
        delivery_zone_price = _active_zone_price(data["delivery_zone_id"])
        if not delivery_zone_price:
            return jsonify({"error": "Active delivery price not found for zone"}), 400
        delivery_zone = delivery_zone_price.delivery_zone
        delivery_fee_suggested = money(delivery_zone_price.fee_amount)
        delivery_fee_final = money(data.get("delivery_fee_final", delivery_fee_suggested))
    elif data.get("delivery_fee_final") is not None:
        delivery_fee_final = money(data["delivery_fee_final"])

    order = Order(
        client_id=data["client_id"],
        client_address_id=data.get("client_address_id"),
        pricing_profile_id=pricing_profile.id if pricing_profile else None,
        payment_type_id=payment_type.id,
        delivery_zone_id=delivery_zone.id if delivery_zone else None,
        delivery_zone_price_id=delivery_zone_price.id if delivery_zone_price else None,
        status=data["status"],
        delivery_fee_suggested=delivery_fee_suggested,
        delivery_fee_final=delivery_fee_final,
        delivery_fee_override_by_user_id=(
            current_user_id if delivery_fee_final != delivery_fee_suggested else None
        ),
        delivery_fee_override_reason=(
            data.get("delivery_fee_override_reason") if delivery_fee_final != delivery_fee_suggested else None
        ),
        global_discount_amount=money(data.get("global_discount_amount", 0)),
        global_discount_reason=data.get("global_discount_reason"),
        payment_type_name_snapshot=payment_type.name,
        payment_surcharge_type_snapshot=payment_type.surcharge_type,
        payment_surcharge_value_snapshot=payment_type.surcharge_value,
        notes=data.get("notes"),
        charged_by_user_id=charged_by_user_id,
        created_by_user_id=current_user_id,
        updated_by_user_id=current_user_id,
    )
    db.session.add(order)
    db.session.flush()

    try:
        item_models, snapshot_models, service_subtotal = _build_order_items(
            order,
            data["items"],
            pricing_profile,
            current_user_id,
        )
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    if item_models is None:
        db.session.rollback()
        payload, status_code = service_subtotal
        return jsonify(payload), status_code

    try:
        extra_models, extras_subtotal, extras_error = _build_extra_items(data.get("extras", []))
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    if extras_error:
        db.session.rollback()
        payload, status_code = extras_error
        return jsonify(payload), status_code

    order.items = item_models
    order.extra_items = extra_models
    db.session.flush()

    for item, snapshot in snapshot_models:
        snapshot.order_item_id = item.id
        item.weight_pricing_snapshot = snapshot
        db.session.add(snapshot)

    order.service_subtotal = money(service_subtotal)
    order.extras_subtotal = money(extras_subtotal)
    order.subtotal_before_payment_surcharge = money(
        order.service_subtotal
        + order.extras_subtotal
        + order.delivery_fee_final
        - money(order.global_discount_amount)
    )
    if order.subtotal_before_payment_surcharge < 0:
        db.session.rollback()
        return jsonify({"error": "global_discount_amount cannot exceed order total"}), 400
    order.payment_surcharge_amount = _calculate_payment_surcharge(order.subtotal_before_payment_surcharge, payment_type)
    order.total_amount = money(order.subtotal_before_payment_surcharge + order.payment_surcharge_amount)

    _create_status_history(order, None, order.status, current_user_id, "Initial status")
    db.session.commit()

    item = _order_query().filter(Order.id == order.id).first_or_404()
    return jsonify(schema.dump(item)), 201


@order_v2_bp.route("/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update(item_id):
    item = _order_query().filter(Order.id == item_id).first_or_404()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = patch_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    current_user_id = get_jwt_identity()
    old_status = item.status

    if "charged_by_user_id" in data:
        user_error = _validate_user(data["charged_by_user_id"], "charged_by")
        if user_error:
            payload, status_code = user_error
            return jsonify(payload), status_code
        item.charged_by_user_id = data["charged_by_user_id"]

    payment_type = item.payment_type
    if "payment_type_id" in data:
        payment_type, payment_type_error = _validate_payment_type(data["payment_type_id"])
        if payment_type_error:
            payload, status_code = payment_type_error
            return jsonify(payload), status_code
        item.payment_type_id = payment_type.id
        item.payment_type_name_snapshot = payment_type.name
        item.payment_surcharge_type_snapshot = payment_type.surcharge_type
        item.payment_surcharge_value_snapshot = payment_type.surcharge_value

    if "delivery_fee_final" in data:
        new_delivery_fee = money(data["delivery_fee_final"])
        item.delivery_fee_final = new_delivery_fee
        if new_delivery_fee != item.delivery_fee_suggested:
            item.delivery_fee_override_by_user_id = current_user_id
            item.delivery_fee_override_reason = data.get("delivery_fee_override_reason")
        else:
            item.delivery_fee_override_by_user_id = None
            item.delivery_fee_override_reason = None

    if "delivery_fee_override_reason" in data and "delivery_fee_final" not in data:
        item.delivery_fee_override_reason = data["delivery_fee_override_reason"]

    if "global_discount_amount" in data:
        item.global_discount_amount = money(data["global_discount_amount"])
    if "global_discount_reason" in data:
        item.global_discount_reason = data["global_discount_reason"]
    if "notes" in data:
        item.notes = data["notes"]
    if "status" in data:
        item.status = data["status"]

    item.updated_by_user_id = current_user_id
    item.subtotal_before_payment_surcharge = money(
        money(item.service_subtotal)
        + money(item.extras_subtotal)
        + money(item.delivery_fee_final)
        - money(item.global_discount_amount)
    )
    if item.subtotal_before_payment_surcharge < 0:
        return jsonify({"error": "global_discount_amount cannot exceed order total"}), 400
    item.payment_surcharge_amount = _calculate_payment_surcharge(item.subtotal_before_payment_surcharge, payment_type)
    item.total_amount = money(item.subtotal_before_payment_surcharge + item.payment_surcharge_amount)

    if old_status != item.status:
        _create_status_history(item, old_status, item.status, current_user_id, "Status update")

    db.session.commit()
    refreshed = _order_query().filter(Order.id == item.id).first_or_404()
    return jsonify(schema.dump(refreshed)), 200
