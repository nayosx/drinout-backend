import json
import math
from decimal import Decimal, ROUND_HALF_UP


MONEY_STEP = Decimal("0.01")
WEIGHT_STEP = Decimal("0.01")


def to_decimal(value, places=MONEY_STEP):
    if value is None:
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    else:
        decimal_value = Decimal(str(value))
    return decimal_value.quantize(places, rounding=ROUND_HALF_UP)


class WeightPricingEngine:
    def __init__(self, profile):
        self.profile = profile
        self.extra_lb_price = to_decimal(profile.extra_lb_price)
        self.round_mode = profile.round_mode or "exact"
        self.strategy = profile.strategy or "MAX_REVENUE"
        self.tiers = [tier for tier in profile.tiers if tier.is_active]
        self.tiers.sort(key=lambda item: (to_decimal(item.max_weight_lb, WEIGHT_STEP), item.sort_order, item.id))

    @classmethod
    def from_profile_id(cls, profile_id=None):
        from models.weight_pricing_profile import WeightPricingProfile

        if profile_id:
            profile = WeightPricingProfile.query.get_or_404(profile_id)
        else:
            profile = (
                WeightPricingProfile.query.filter_by(is_active=True)
                .order_by(WeightPricingProfile.id.asc())
                .first()
            )
            if not profile:
                raise ValueError("No active weight pricing profile found")
        return cls(profile)

    def quote(self, weight_lb):
        weight = to_decimal(weight_lb, WEIGHT_STEP)
        if weight is None or weight <= 0:
            raise ValueError("weight_lb must be greater than 0")
        if not self.tiers:
            raise ValueError("The selected profile has no active tiers")

        options = self._build_options(weight)
        selected = self._select_option(weight, options)
        serialized_options = [self._serialize_option(option, selected["key"]) for option in options]
        lowest = min(option["total_price"] for option in options)
        highest = max(option["total_price"] for option in options)
        decision_reason = self._build_decision_reason(weight, selected, serialized_options, lowest, highest)

        return {
            "profile_id": self.profile.id,
            "profile_name": self.profile.name,
            "weight_lb": str(weight),
            "strategy_selected": self.strategy,
            "selected_price": str(selected["total_price"]),
            "recommended_price": str(selected["total_price"]),
            "selected_tier_id": selected["tier"].id if selected["tier"] else None,
            "selected_tier_max_weight_lb": (
                str(to_decimal(selected["tier"].max_weight_lb, WEIGHT_STEP))
                if selected["tier"]
                else None
            ),
            "selected_option_type": selected["option_type"],
            "selected_base_price": str(selected["tier_price"]) if selected["tier_price"] is not None else None,
            "allow_manual_override": self.profile.allow_manual_override,
            "decision_reason": decision_reason,
            "options_evaluated": serialized_options,
            "lowest_valid_price": str(lowest),
            "highest_valid_price": str(highest),
            "difference_selected_vs_lowest": str(to_decimal(selected["total_price"] - lowest)),
            "difference_selected_vs_highest": str(to_decimal(highest - selected["total_price"])),
            "compare_all_tiers": self.profile.compare_all_tiers,
            "round_mode": self.round_mode,
            "evaluated_options_count": len(serialized_options),
            "options_evaluated_json": json.dumps(serialized_options, ensure_ascii=True),
        }

    def _build_options(self, weight):
        covering_tier = next((tier for tier in self.tiers if to_decimal(tier.max_weight_lb, WEIGHT_STEP) >= weight), None)
        lower_tiers = [tier for tier in self.tiers if to_decimal(tier.max_weight_lb, WEIGHT_STEP) <= weight]
        base_tier = lower_tiers[-1] if lower_tiers else None
        options = []

        if covering_tier:
            options.append(self._make_tier_option(covering_tier, "BEST_TIER_FIT", weight))
        if base_tier:
            options.append(self._make_base_plus_extra_option(base_tier, weight))
        elif covering_tier:
            options.append(self._make_tier_option(covering_tier, "MIN_TIER_COVERAGE", weight))

        if self.profile.compare_all_tiers:
            for tier in self.tiers:
                tier_weight = to_decimal(tier.max_weight_lb, WEIGHT_STEP)
                if tier_weight >= weight:
                    options.append(self._make_tier_option(tier, "ALL_TIERS_COVERAGE", weight))
                else:
                    options.append(self._make_base_plus_extra_option(tier, weight, option_type="ALL_TIERS_BASE_PLUS_EXTRA"))

        deduped = []
        seen = set()
        for option in options:
            key = option["key"]
            if key in seen:
                continue
            seen.add(key)
            deduped.append(option)
        return deduped

    def _make_tier_option(self, tier, option_type, weight):
        tier_price = to_decimal(tier.price)
        tier_weight = to_decimal(tier.max_weight_lb, WEIGHT_STEP)
        reason = f"Tier {tier_weight} lb cubre el peso {weight} lb con precio fijo {tier_price}."
        return {
            "key": f"{option_type}:{tier.id}:{tier_price}",
            "option_type": option_type,
            "tier": tier,
            "tier_price": tier_price,
            "extra_lb": to_decimal(0, WEIGHT_STEP),
            "extra_charge": to_decimal(0),
            "total_price": tier_price,
            "reason": reason,
        }

    def _make_base_plus_extra_option(self, tier, weight, option_type="BASE_PLUS_EXTRA"):
        tier_price = to_decimal(tier.price)
        tier_weight = to_decimal(tier.max_weight_lb, WEIGHT_STEP)
        extra_lb = weight - tier_weight
        if extra_lb < 0:
            extra_lb = Decimal("0.00")
        rounded_extra_lb = self._round_extra_lb(extra_lb)
        extra_charge = to_decimal(rounded_extra_lb * self.extra_lb_price)
        total_price = to_decimal(tier_price + extra_charge)
        reason = (
            f"Base {tier_weight} lb con {rounded_extra_lb} lb extra a {self.extra_lb_price} "
            f"da total {total_price}."
        )
        return {
            "key": f"{option_type}:{tier.id}:{total_price}",
            "option_type": option_type,
            "tier": tier,
            "tier_price": tier_price,
            "extra_lb": rounded_extra_lb,
            "extra_charge": extra_charge,
            "total_price": total_price,
            "reason": reason,
        }

    def _round_extra_lb(self, extra_lb):
        if self.round_mode == "ceil":
            return Decimal(str(math.ceil(float(extra_lb))))
        if self.round_mode == "floor":
            return Decimal(str(math.floor(float(extra_lb))))
        return to_decimal(extra_lb, WEIGHT_STEP)

    def _select_option(self, weight, options):
        sorted_by_total = sorted(options, key=lambda option: (option["total_price"], option["tier"].id if option["tier"] else 0))
        best_tier_fit = next(
            (
                option
                for option in options
                if option["option_type"] in {"BEST_TIER_FIT", "ALL_TIERS_COVERAGE", "MIN_TIER_COVERAGE"}
                and to_decimal(option["tier"].max_weight_lb, WEIGHT_STEP) >= weight
            ),
            None,
        )
        base_plus_extra = next(
            (
                option
                for option in options
                if option["option_type"] in {"BASE_PLUS_EXTRA", "ALL_TIERS_BASE_PLUS_EXTRA"}
            ),
            None,
        )
        highest = max(options, key=lambda option: (option["total_price"], option["tier"].id if option["tier"] else 0))
        lowest = min(options, key=lambda option: (option["total_price"], option["tier"].id if option["tier"] else 0))

        if self.strategy == "MAX_REVENUE":
            selected = highest
            selected["reason"] = (
                f"Estrategia MAX_REVENUE: se evaluaron todas las alternativas validas y se eligio el mayor total "
                f"permitido {selected['total_price']}."
            )
            return selected

        if self.strategy == "CUSTOMER_BEST_PRICE":
            selected = lowest
            selected["reason"] = (
                f"Estrategia CUSTOMER_BEST_PRICE: se eligio la alternativa mas baja {selected['total_price']}."
            )
            return selected

        if self.strategy == "BASE_PLUS_EXTRA" and base_plus_extra:
            selected = base_plus_extra
            selected["reason"] = (
                f"Estrategia BASE_PLUS_EXTRA: se uso el tier base mas cercano y se agregaron libras extra."
            )
            return selected

        if self.strategy == "PROMOTIONAL_UPGRADE" and best_tier_fit:
            selected = best_tier_fit
            if self.profile.auto_upgrade_enabled:
                upper_options = [
                    option
                    for option in options
                    if option["tier"]
                    and to_decimal(option["tier"].max_weight_lb, WEIGHT_STEP)
                    > to_decimal(best_tier_fit["tier"].max_weight_lb, WEIGHT_STEP)
                    and option["option_type"] in {"BEST_TIER_FIT", "ALL_TIERS_COVERAGE"}
                ]
                if upper_options:
                    upper = min(
                        upper_options,
                        key=lambda option: to_decimal(option["tier"].max_weight_lb, WEIGHT_STEP),
                    )
                    margin = to_decimal(upper["total_price"] - best_tier_fit["total_price"])
                    allowed_margin = to_decimal(self.profile.auto_upgrade_margin or 0)
                    if margin <= allowed_margin:
                        upper["reason"] = (
                            f"Estrategia PROMOTIONAL_UPGRADE: se promovio al tier superior dentro del margen {allowed_margin}."
                        )
                        return upper
            selected["reason"] = "Estrategia PROMOTIONAL_UPGRADE: no aplico promocion, se uso el best tier fit."
            return selected

        if self.strategy == "FORCE_UPGRADE_FROM_WEIGHT" and best_tier_fit:
            threshold = to_decimal(self.profile.force_upgrade_from_lb, WEIGHT_STEP) if self.profile.force_upgrade_from_lb is not None else None
            if threshold is not None and weight >= threshold:
                upper_options = [
                    option
                    for option in options
                    if option["tier"]
                    and to_decimal(option["tier"].max_weight_lb, WEIGHT_STEP)
                    > to_decimal(best_tier_fit["tier"].max_weight_lb, WEIGHT_STEP)
                    and option["option_type"] in {"BEST_TIER_FIT", "ALL_TIERS_COVERAGE"}
                ]
                if upper_options:
                    upper = min(
                        upper_options,
                        key=lambda option: to_decimal(option["tier"].max_weight_lb, WEIGHT_STEP),
                    )
                    upper["reason"] = (
                        f"Estrategia FORCE_UPGRADE_FROM_WEIGHT: el peso {weight} supera el umbral {threshold} "
                        f"y se fuerza tier superior."
                    )
                    return upper
            best_tier_fit["reason"] = "Estrategia FORCE_UPGRADE_FROM_WEIGHT: no se activo el umbral, se usa best tier fit."
            return best_tier_fit

        if best_tier_fit:
            best_tier_fit["reason"] = "Estrategia BEST_TIER_FIT: se eligio el tier minimo que cubre el peso."
            return best_tier_fit

        return highest

    def _serialize_option(self, option, selected_key):
        return {
            "option_type": option["option_type"],
            "tier_id": option["tier"].id if option["tier"] else None,
            "tier_max_weight_lb": (
                str(to_decimal(option["tier"].max_weight_lb, WEIGHT_STEP))
                if option["tier"]
                else None
            ),
            "tier_price": str(option["tier_price"]) if option["tier_price"] is not None else None,
            "extra_lb": str(option["extra_lb"]),
            "extra_charge": str(option["extra_charge"]),
            "total_price": str(option["total_price"]),
            "reason": option["reason"],
            "selected": option["key"] == selected_key,
        }

    def _build_decision_reason(self, weight, selected, serialized_options, lowest, highest):
        selected_total = to_decimal(selected["total_price"])
        option_summaries = ", ".join(
            f"{option['option_type']}={option['total_price']}"
            for option in serialized_options
        )
        return (
            f"Perfil '{self.profile.name}' con estrategia {self.strategy} para peso {weight} lb. "
            f"Se evaluaron {len(serialized_options)} alternativas: {option_summaries}. "
            f"La alternativa seleccionada fue {selected['option_type']} con total {selected_total}. "
            f"El minimo valido fue {to_decimal(lowest)} y el maximo valido fue {to_decimal(highest)}. "
            f"Motivo comercial: {selected['reason']}"
        )
