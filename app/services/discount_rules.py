from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from models.discount_rule import DiscountRule


def _money(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    else:
        decimal_value = Decimal(str(value))
    return decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _as_whole_quantity(quantity):
    if quantity is None:
        return None
    if isinstance(quantity, Decimal):
        decimal_quantity = quantity
    else:
        decimal_quantity = Decimal(str(quantity))
    if decimal_quantity != decimal_quantity.to_integral_value():
        return None
    return int(decimal_quantity)


def _select_active_rule(item, at_time=None):
    if not item.service_id:
        return None

    now = at_time or datetime.now(timezone.utc).replace(tzinfo=None)
    candidate_rules = (
        DiscountRule.query
        .filter(DiscountRule.service_id == item.service_id)
        .filter(DiscountRule.is_active.is_(True))
        .filter(
            (DiscountRule.starts_at.is_(None)) | (DiscountRule.starts_at <= now)
        )
        .filter(
            (DiscountRule.ends_at.is_(None)) | (DiscountRule.ends_at >= now)
        )
        .order_by(
            DiscountRule.priority.desc(),
            DiscountRule.service_variant_id.desc(),
            DiscountRule.id.asc(),
        )
        .all()
    )

    quantity_int = _as_whole_quantity(item.quantity)
    if quantity_int is None or quantity_int <= 0:
        return None

    for rule in candidate_rules:
        if rule.service_variant_id is not None and rule.service_variant_id != item.service_variant_id:
            continue
        if quantity_int < int(rule.min_quantity or 1):
            continue
        return rule
    return None


def _apply_package_price(rule, quantity_int, unit_catalog_price):
    block_quantity = int(rule.block_quantity or rule.min_quantity or 0)
    if block_quantity <= 0:
        return None

    block_price = _money(rule.discount_value)
    catalog_subtotal = _money(Decimal(quantity_int) * unit_catalog_price)

    if rule.application_mode == DiscountRule.APPLICATION_MODE_EXACT:
        if quantity_int != block_quantity:
            return None
        final_price = block_price
        full_blocks = 1
        remainder_units = 0
    elif rule.application_mode == DiscountRule.APPLICATION_MODE_ONE_TIME:
        if quantity_int < block_quantity:
            return None
        remainder_units = quantity_int - block_quantity
        final_price = _money(block_price + (Decimal(remainder_units) * unit_catalog_price))
        full_blocks = 1
    elif rule.application_mode == DiscountRule.APPLICATION_MODE_PER_BLOCK:
        full_blocks = quantity_int // block_quantity
        if full_blocks <= 0:
            return None
        remainder_units = quantity_int % block_quantity
        final_price = _money(
            (Decimal(full_blocks) * block_price) + (Decimal(remainder_units) * unit_catalog_price)
        )
    else:
        return None

    saved_amount = _money(catalog_subtotal - final_price)
    if saved_amount <= Decimal("0.00"):
        return None

    return {
        "catalog_price": catalog_subtotal,
        "applied_price": final_price,
        "discount_amount": saved_amount,
        "rule": {
            "id": rule.id,
            "name": rule.name,
            "discount_type": rule.discount_type,
            "application_mode": rule.application_mode,
            "min_quantity": int(rule.min_quantity or 1),
            "block_quantity": block_quantity,
            "discount_value": f"{block_price:.2f}",
            "full_blocks": full_blocks,
            "remainder_units": remainder_units,
        },
    }


def _apply_percentage(rule, quantity_int, unit_catalog_price):
    percentage = _money(rule.discount_value)
    catalog_subtotal = _money(Decimal(quantity_int) * unit_catalog_price)
    if percentage <= Decimal("0.00"):
        return None

    if rule.application_mode == DiscountRule.APPLICATION_MODE_EXACT and quantity_int != int(rule.min_quantity or 1):
        return None

    multiplier = _money(percentage / Decimal("100"))
    discount_amount = _money(catalog_subtotal * multiplier)
    final_price = _money(catalog_subtotal - discount_amount)
    if discount_amount <= Decimal("0.00"):
        return None

    return {
        "catalog_price": catalog_subtotal,
        "applied_price": final_price,
        "discount_amount": discount_amount,
        "rule": {
            "id": rule.id,
            "name": rule.name,
            "discount_type": rule.discount_type,
            "application_mode": rule.application_mode,
            "min_quantity": int(rule.min_quantity or 1),
            "block_quantity": int(rule.block_quantity or 0) or None,
            "discount_value": f"{percentage:.2f}",
            "full_blocks": None,
            "remainder_units": None,
        },
    }


def _apply_fixed_amount(rule, quantity_int, unit_catalog_price):
    amount = _money(rule.discount_value)
    catalog_subtotal = _money(Decimal(quantity_int) * unit_catalog_price)
    if amount <= Decimal("0.00"):
        return None

    if rule.application_mode == DiscountRule.APPLICATION_MODE_EXACT and quantity_int != int(rule.min_quantity or 1):
        return None

    if rule.application_mode == DiscountRule.APPLICATION_MODE_PER_BLOCK:
        block_quantity = int(rule.block_quantity or rule.min_quantity or 0)
        if block_quantity <= 0:
            return None
        full_blocks = quantity_int // block_quantity
        if full_blocks <= 0:
            return None
        discount_amount = _money(Decimal(full_blocks) * amount)
        remainder_units = quantity_int % block_quantity
    else:
        full_blocks = 1
        remainder_units = 0
        discount_amount = amount

    final_price = _money(catalog_subtotal - discount_amount)
    if discount_amount <= Decimal("0.00") or final_price < Decimal("0.00"):
        return None

    return {
        "catalog_price": catalog_subtotal,
        "applied_price": final_price,
        "discount_amount": discount_amount,
        "rule": {
            "id": rule.id,
            "name": rule.name,
            "discount_type": rule.discount_type,
            "application_mode": rule.application_mode,
            "min_quantity": int(rule.min_quantity or 1),
            "block_quantity": int(rule.block_quantity or 0) or None,
            "discount_value": f"{amount:.2f}",
            "full_blocks": full_blocks,
            "remainder_units": remainder_units,
        },
    }


def calculate_commercial_discount(item, unit_catalog_price, at_time=None):
    if unit_catalog_price is None:
        return None

    quantity_int = _as_whole_quantity(item.quantity)
    if quantity_int is None or quantity_int <= 0:
        return None

    rule = _select_active_rule(item, at_time=at_time)
    if rule is None:
        return None

    if rule.discount_type == DiscountRule.DISCOUNT_TYPE_PACKAGE_PRICE:
        return _apply_package_price(rule, quantity_int, unit_catalog_price)
    if rule.discount_type == DiscountRule.DISCOUNT_TYPE_PERCENTAGE:
        return _apply_percentage(rule, quantity_int, unit_catalog_price)
    if rule.discount_type == DiscountRule.DISCOUNT_TYPE_FIXED_AMOUNT:
        return _apply_fixed_amount(rule, quantity_int, unit_catalog_price)
    return None
