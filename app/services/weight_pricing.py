from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Optional


MONEY_PLACES = Decimal("0.01")


def _as_decimal(value: Any, default: Optional[str] = None) -> Decimal:
    if value is None:
        if default is None:
            raise ValueError("A decimal value is required")
        return Decimal(str(default))
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money(value: Any) -> Decimal:
    return _as_decimal(value).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _decimal_to_str(value: Any) -> str:
    return format(_money(value), ".2f")


def _find_active_tiers(tiers: Iterable[Any]) -> list[Any]:
    active = [tier for tier in tiers if getattr(tier, "is_active", True)]
    return sorted(active, key=lambda tier: (getattr(tier, "sort_order", 0), getattr(tier, "id", 0)))


class WeightPricingEngine:
    def __init__(self, profile: Any):
        self.profile = profile
        self.tiers = _find_active_tiers(getattr(profile, "tiers", []))
        if not self.tiers:
            raise ValueError("Weight pricing profile requires at least one active tier")

    def quote(self, weight_lb: Any) -> Dict[str, Any]:
        weight = _as_decimal(weight_lb)
        if weight <= 0:
            raise ValueError("weight_lb must be greater than zero")

        strategy = (getattr(self.profile, "strategy", "PACKAGE_BLOCKS") or "PACKAGE_BLOCKS").upper()
        if strategy == "PACKAGE_BLOCKS":
            return self._quote_package_blocks(weight)
        return self._quote_max_revenue(weight)

    def _quote_max_revenue(self, weight: Decimal) -> Dict[str, Any]:
        extra_lb_price = _as_decimal(getattr(self.profile, "extra_lb_price", "0.00"), "0.00")
        options = []
        best_tier_fit_prices = []
        base_plus_extra_prices = []

        for tier in self.tiers:
            tier_weight = _as_decimal(getattr(tier, "max_weight_lb"))
            tier_price = _money(getattr(tier, "price"))
            if weight <= tier_weight:
                best_fit_option = {
                    "option_type": "BEST_TIER_FIT",
                    "tier_id": getattr(tier, "id", None),
                    "tier_max_weight_lb": _decimal_to_str(tier_weight),
                    "price": _decimal_to_str(tier_price),
                    "extra_lb": _decimal_to_str("0.00"),
                    "extra_charge": _decimal_to_str("0.00"),
                }
                options.append(best_fit_option)
                best_tier_fit_prices.append(tier_price)

            base_price = tier_price
            extra_lb = max(weight - tier_weight, Decimal("0.00"))
            extra_charge = _money(extra_lb * extra_lb_price)
            total_price = _money(base_price + extra_charge)
            base_option = {
                "option_type": "BASE_PLUS_EXTRA",
                "tier_id": getattr(tier, "id", None),
                "tier_max_weight_lb": _decimal_to_str(tier_weight),
                "price": _decimal_to_str(total_price),
                "extra_lb": _decimal_to_str(extra_lb),
                "extra_charge": _decimal_to_str(extra_charge),
            }
            options.append(base_option)
            base_plus_extra_prices.append(total_price)

        selected = max(options, key=lambda option: Decimal(option["price"]))
        lowest = min(Decimal(option["price"]) for option in options)
        highest = max(Decimal(option["price"]) for option in options)
        strategy_name = (getattr(self.profile, "strategy", "MAX_REVENUE") or "MAX_REVENUE").upper()

        decision_parts = []
        if best_tier_fit_prices:
            decision_parts.append(f"BEST_TIER_FIT={_decimal_to_str(max(best_tier_fit_prices))}")
        if base_plus_extra_prices:
            decision_parts.append(f"ALL_TIERS_BASE_PLUS_EXTRA={_decimal_to_str(max(base_plus_extra_prices))}")
        decision_reason = f"{strategy_name}: " + ", ".join(decision_parts)

        return {
            "selected_price": selected["price"],
            "recommended_price": selected["price"],
            "selected_option_type": selected["option_type"],
            "selected_tier_id": selected["tier_id"],
            "selected_tier_max_weight_lb": selected["tier_max_weight_lb"],
            "highest_valid_price": _decimal_to_str(highest),
            "lowest_valid_price": _decimal_to_str(lowest),
            "difference_selected_vs_highest": _decimal_to_str(Decimal(selected["price"]) - highest),
            "difference_selected_vs_lowest": _decimal_to_str(Decimal(selected["price"]) - lowest),
            "allow_manual_override": bool(getattr(self.profile, "allow_manual_override", False)),
            "evaluated_options_count": len(options),
            "decision_reason": decision_reason,
            "options_evaluated": options,
        }

    def _quote_package_blocks(self, weight: Decimal) -> Dict[str, Any]:
        tiers_by_weight = {int(_as_decimal(tier.max_weight_lb)): tier for tier in self.tiers}
        tier_15 = tiers_by_weight.get(15)
        tier_25 = tiers_by_weight.get(25)
        if not tier_15 or not tier_25:
            raise ValueError("PACKAGE_BLOCKS strategy requires active 15 lb and 25 lb tiers")

        tier_15_price = _money(tier_15.price)
        tier_25_price = _money(tier_25.price)
        extra_lb_price = _as_decimal(getattr(self.profile, "extra_lb_price", "0.00"), "0.00")

        blocks_25 = int((weight / Decimal("25")).to_integral_value(rounding=ROUND_FLOOR))
        remainder = weight - (Decimal(blocks_25) * Decimal("25"))

        decision_bits = [f"{blocks_25} bloque(s) de 25 lb"]
        charged_25_blocks = blocks_25
        charged_15_blocks = 0
        extra_lb = Decimal("0.00")

        if remainder == Decimal("0.00"):
            pass
        elif remainder >= Decimal("20.00"):
            charged_25_blocks += 1
            decision_bits.append("remanente >= 20 lb redondeado a bloque de 25 lb")
            remainder = Decimal("0.00")
        elif remainder >= Decimal("15.00"):
            charged_15_blocks += 1
            extra_lb = remainder - Decimal("15.00")
            decision_bits.append("1 bloque(s) de 15 lb")
            if extra_lb > 0:
                decision_bits.append(f"{_decimal_to_str(extra_lb)} lb extra")
        elif remainder >= Decimal("8.00"):
            charged_15_blocks += 1
            decision_bits.append("remanente redondeado a bloque de 15 lb")
            remainder = Decimal("0.00")
        else:
            extra_lb = remainder
            decision_bits.append(f"{_decimal_to_str(extra_lb)} lb extra")

        extra_charge = _money(extra_lb * extra_lb_price)
        selected_price = _money(
            (Decimal(charged_25_blocks) * tier_25_price)
            + (Decimal(charged_15_blocks) * tier_15_price)
            + extra_charge
        )

        option = {
            "option_type": "PACKAGE_BLOCKS",
            "tier_id": getattr(tier_25, "id", None),
            "tier_max_weight_lb": _decimal_to_str("25.00"),
            "price": _decimal_to_str(selected_price),
            "extra_lb": _decimal_to_str(extra_lb),
            "extra_charge": _decimal_to_str(extra_charge),
        }

        return {
            "selected_price": option["price"],
            "recommended_price": option["price"],
            "selected_option_type": "PACKAGE_BLOCKS",
            "selected_tier_id": getattr(tier_25, "id", None),
            "selected_tier_max_weight_lb": option["tier_max_weight_lb"],
            "highest_valid_price": option["price"],
            "lowest_valid_price": option["price"],
            "difference_selected_vs_highest": _decimal_to_str("0.00"),
            "difference_selected_vs_lowest": _decimal_to_str("0.00"),
            "allow_manual_override": bool(getattr(self.profile, "allow_manual_override", False)),
            "evaluated_options_count": 1,
            "decision_reason": "PACKAGE_BLOCKS: " + ", ".join(decision_bits),
            "options_evaluated": [option],
        }


DEFAULT_WEIGHT_PRICING_CONFIG = {
    "tier_1_max_lb": Decimal("15.00"),
    "tier_1_price": Decimal("9.99"),
    "tier_2_max_lb": Decimal("25.00"),
    "tier_2_price": Decimal("14.99"),
    "extra_lb_price": Decimal("0.90"),
    "min_price_no_services": Decimal("9.99"),
}


def normalize_weight_pricing_config(raw_config: Optional[Dict[str, Any]] = None) -> Dict[str, Decimal]:
    raw_config = raw_config or {}
    normalized = {}
    for key, default_value in DEFAULT_WEIGHT_PRICING_CONFIG.items():
        normalized[key] = _money(raw_config.get(key, default_value))
    return normalized


def calculate_weight_service_quote(
    weight_lb: Any,
    has_other_services: bool,
    pricing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    weight = _money(weight_lb)
    if weight <= 0:
        raise ValueError("weight_lb must be greater than zero")

    config = normalize_weight_pricing_config(pricing_config)
    tier_1_max_lb = config["tier_1_max_lb"]
    tier_1_price = config["tier_1_price"]
    tier_2_max_lb = config["tier_2_max_lb"]
    tier_2_price = config["tier_2_price"]
    extra_lb_price = config["extra_lb_price"]
    min_price = config["min_price_no_services"]

    applied_rules = {
        "upgraded_to_25lb": False,
        "upgraded_to_15lb": False,
        "minimum_fee_applied": False,
        "preferential_rate_applied": False,
    }
    charged_as = "Lavado por Peso"

    if Decimal("1.00") <= weight <= Decimal("11.00") and has_other_services:
        friendly_price = _money(weight * extra_lb_price)
        strict_price = friendly_price
        applied_rules["preferential_rate_applied"] = True
        charged_as = "Tarifa Preferencial (Libras Extra)"
    else:
        blocks_25 = int((weight / tier_2_max_lb).to_integral_value(rounding=ROUND_FLOOR))
        remainder_after_25 = weight % tier_2_max_lb

        blocks_15 = int((remainder_after_25 / tier_1_max_lb).to_integral_value(rounding=ROUND_FLOOR))
        extra_lb = remainder_after_25 % tier_1_max_lb

        cost_blocks_25 = _money(Decimal(blocks_25) * tier_2_price)
        cost_blocks_15 = _money(Decimal(blocks_15) * tier_1_price)
        cost_extra_lb = _money(extra_lb * extra_lb_price)
        remainder_cost = _money(cost_blocks_15 + cost_extra_lb)

        strict_price = _money(cost_blocks_25 + remainder_cost)
        friendly_price = strict_price

        if remainder_cost > tier_2_price:
            friendly_price = _money(cost_blocks_25 + tier_2_price)
            applied_rules["upgraded_to_25lb"] = True
            charged_as = f"Promocion {int(tier_2_max_lb)}lb"
        elif remainder_after_25 <= tier_1_max_lb and remainder_cost > tier_1_price:
            friendly_price = _money(cost_blocks_25 + tier_1_price)
            applied_rules["upgraded_to_15lb"] = True
            charged_as = f"Promocion {int(tier_1_max_lb)}lb"

        if not has_other_services and weight <= tier_1_max_lb and friendly_price < min_price:
            friendly_price = min_price
            if strict_price < min_price:
                strict_price = min_price
            applied_rules["minimum_fee_applied"] = True
            charged_as = "Tarifa Minima (Promocion 15lb)"

    total_saved = _money(strict_price - friendly_price)
    return {
        "summary": {
            "final_price": _decimal_to_str(friendly_price),
            "strict_price": _decimal_to_str(strict_price),
            "total_saved": _decimal_to_str(total_saved),
            "is_friendly_applied": friendly_price < strict_price,
        },
        "breakdown": {
            "total_weight": _decimal_to_str(weight),
            "charged_as": charged_as,
            "has_other_services": bool(has_other_services),
        },
        "applied_rules": applied_rules,
        "config_used": {key: _decimal_to_str(value) for key, value in config.items()},
    }
